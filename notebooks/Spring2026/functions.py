import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.cm as cm
import pandas as pd
import geopandas as gpd
import plotly.express as px
import numpy as np
import ast
import textwrap
from matplotlib.ticker import MaxNLocator



def time_filt(df, start, end):
    datetime_start = pd.to_datetime(start)
    datetime_end = pd.to_datetime(end)
    df_copy = df.copy()
    
    df_copy['SPEND_DATE_RANGE_START'] = pd.to_datetime(df_copy['SPEND_DATE_RANGE_START'])
    df_copy['SPEND_DATE_RANGE_END'] = pd.to_datetime(df_copy['SPEND_DATE_RANGE_END'])
    
    df_filtered = df_copy[(df_copy['SPEND_DATE_RANGE_START'] >= datetime_start) &
                                 (df_copy['SPEND_DATE_RANGE_END'] <= datetime_end)]
    
    return df_filtered



def percent_instate(df):
    home_city = df['CUSTOMER_HOME_CITY']
    state_info = [['WY', 0]]
    state_info_close = []
    state_info_big = []

    ## Taking spending data and appending to list for each purchase in POIs
    for val in home_city:
        cities = val.split(",")
        cities = cities[1::2]
        for i in cities:
            found = False
            state = i.split(':')
            state[0] = state[0].strip().strip("\"")
            j = 0
            while j < len(state_info):
                if state[0] == state_info[j][0]:
                    count = state[1].strip("{}")
                    state_info[j][1] = state_info[j][1] + int(count)
                    found = True
                j += 1
            if found == False:
                count = state[1].strip("{}")
                state_info.append([state[0], int(count)])
    state_info = sorted(state_info, key = lambda state: state[0])

    ## Sorting to 5 closest states
    dump1 = ['Other', 0]
    for i in state_info:
        if (i[0] == 'WY' or i[0] == 'CO' or i[0] == 'MT' or i[0] == 'ID' or i[0] == 'SD'):
            state_info_close.append(i)
        else:
            dump1[1] += i[1]
    state_info_close.append(dump1)

    ## Sorting to 5 biggest states
    dump2 = ['Other', 0]
    state_info_big_temp = sorted(state_info, key = lambda state: state[1], reverse = True)
    for i in state_info:
        if (i[0] == state_info_big_temp[0][0] or i[0] == state_info_big_temp[1][0] or i[0] == state_info_big_temp[2][0] or i[0] == state_info_big_temp[3][0] or i[0] == state_info_big_temp[4][0]):
            state_info_big.append(i)
        else:
            dump2[1] += i[1]
    state_info_big.append(dump2)
    
    return [state_info_big, state_info_close, state_info]



def percent_change_month(df):
    pct_change_month = df['SPEND_PCT_CHANGE_VS_PREV_MONTH'].dropna()
    
    sum = 0
    product = 1
    for val in pct_change_month:
        sum += val/100
        product *= val/100
    pct_change_total = (sum + product)*100
    return pct_change_total



def percent_change_year(df):
    pct_change_year = df['SPEND_PCT_CHANGE_VS_PREV_YEAR'].dropna()
    
    sum = 0
    product = 1
    for val in pct_change_year:
        sum += val/100
        product *= val/100
    pct_change_total = (sum + product)*100
    return pct_change_total



def spend_by_day(df):
    df_filtered = df.copy()

    # Convert string representations of lists in 'SPEND_BY_DAY' to actual lists
    df_filtered['SPEND_BY_DAY'] = df_filtered['SPEND_BY_DAY'].apply(ast.literal_eval)

    # Add a new column called 'DATE_OF_MONTH', as a list of integers from 1 to the end of the month (length of the 'SPEND_BY_DAY' list)
    df_filtered['DATE_OF_MONTH'] = df_filtered['SPEND_BY_DAY'].apply(lambda x: list(range(1, len(x) + 1)))

    df_spend_by_day = df_filtered.explode(['SPEND_BY_DAY', 'DATE_OF_MONTH'])

    df_spend_by_day['SPEND_BY_DAY'] = df_spend_by_day['SPEND_BY_DAY'].astype(float)
    df_spend_by_day['DATE_OF_MONTH'] = df_spend_by_day['DATE_OF_MONTH'].astype(int)

    df_spend_by_day['DATE'] = pd.to_datetime(df_spend_by_day['SPEND_DATE_RANGE_START']) + pd.to_timedelta(df_spend_by_day['DATE_OF_MONTH'] - 1, unit='D')

    df_grouped = df_spend_by_day.groupby('DATE')['SPEND_BY_DAY'].sum()

    return df_grouped



def type_pie_town(df_safegraph_poi, df_safegraph_spend, place):
    ## Make DataFrame for POIs in slected town/towns
    combined_mask = np.zeros(len(df_safegraph_poi), dtype = bool)
    if type(place) == list:
        for i in place:
            mask = df_safegraph_poi['CITY'] == i
            combined_mask += mask
        df_place = df_safegraph_poi[combined_mask]
    else:
        mask = df_safegraph_poi['CITY'] == place
        df_place = df_safegraph_poi[mask]

    ## NAICS code groupings for pie chart
    groups = {
            'Construction' : [['23'], 'Orange', []],
            'Manufacturing' : [['31', '32', '33'], 'Yellow', []],
            'Retail' : [['44', '45'], 'Lightcoral', []],
            'Transportation' : [['48', '49'], 'Royalblue', []],
            'Real Estate' : [['53'], 'Purple', []],
            'Technical Services' : [['54'], 'Red', []],
            'Administrative Services' : [['56'], 'Peru', []],
            'Health Care' : [['62'], 'Hotpink', []],
            'Arts' : [['71'], 'Aqua', []],
            'Accomodations and Food' : [['72'], 'Springgreen', []],
            'Other' : [['81', '55', '21', '52', '61', '51', '42', '22', '11'], 'Gold', []],
            'Public Administration' : [['92'], 'Indigo', []]
        }

    #print("Here is unfiltered number of POIs", len(df_place))

    ## Make a DataFrame for our 2 character codes
    naics_to_group = {}
    for group_name, code_list in groups.items():
        for code in code_list[0]:
            naics_to_group[code] = group_name

    ## Getting data and putting it in readable form for the pie chart
    df_place['NAICS_CODE_FINAL'] = df_place['NAICS_CODE'].astype(str).str[:2].map(lambda x: naics_to_group.get(x, 'Dump'))
    naics_codes = df_place['NAICS_CODE_FINAL'].value_counts()

    ## This code is for making pie charts about specific spending at NAICS codes
    #fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    #ax1.pie(naics_codes, colors = [groups[label][1] for label in naics_codes.index])
    #fig.legend()
    #if type(place) == list:
    #        #title = ''
    #        #for i in place:
    #        #    title += i + ', '
    #        ax1.set_title('Total POIs')
    #else:
    #    ax1.set_title('POIs in ' + place)
    ##fig.legend(naics_codes.index, fontsize = 'small')
    #
    ## Repeat process for specific POIs that had credit card spending at them
    if 'PLACEKEY' in df_safegraph_spend.columns and 'PLACEKEY' in df_place.columns:
        df_pie = df_place[df_place['PLACEKEY'].isin(df_safegraph_spend['PLACEKEY'])]
    
        naics_to_group = {}
        for group_name, code_list in groups.items():
            for code in code_list[0]:
                naics_to_group[code] = group_name
    
        df_pie['NAICS_CODE_FINAL'] = df_pie['NAICS_CODE'].astype(str).str[:2].map(lambda x: naics_to_group.get(x, 'Other'))
    #    naics_codes_filtered = df_pie['NAICS_CODE_FINAL'].value_counts()
    #    
    #    ax2.pie(naics_codes_filtered, colors = [groups[label][1] for label in naics_codes_filtered.index])
    #    if type(place) == list:
    #        title = ''
    #        for i in place:
    #            title += i + ', '
    #        ax2.set_title('POIs with spending')
    #    else:
    #        ax2.set_title('POIs with spending in ' + place)
        
    return [df_pie, groups]



def total_POIs(df_safegraph_poi, df_safegraph_spend, places, start, end):
    plt.rcParams['axes.labelsize'] = 20
    plt.rcParams['xtick.labelsize'] = 20
    plt.rcParams['ytick.labelsize'] = 25
    plt.rcParams['axes.titlesize'] = 30
    ## Make DataFrame for POIs in slected town/towns
    combined_mask = np.zeros(len(df_safegraph_poi), dtype = bool)
    for i in places:
        if type(i) == list:
            for f in i:
                mask = df_safegraph_poi['CITY'] == f
                combined_mask += mask
        else:
            mask = df_safegraph_poi['CITY'] == i
            combined_mask += mask
    df_place = df_safegraph_poi[combined_mask]

    ## NAICS code groupings for chart
    groups = {
            'Construction' : [['23'], 'Orange', []],
            'Manufacturing' : [['31', '32', '33'], 'Yellow', []],
            'Retail' : [['44', '45'], 'Lightcoral', []],
            'Transportation' : [['48', '49'], 'Royalblue', []],
            'Real Estate' : [['53'], 'Purple', []],
            'Technical Services' : [['54'], 'Red', []],
            'Administrative Services' : [['56'], 'Peru', []],
            'Health Care' : [['62'], 'Hotpink', []],
            'Arts' : [['71'], 'Aqua', []],
            'Accomodations and Food' : [['72'], 'Springgreen', []],
            'Other' : [['81', '55', '21', '52', '61', '51', '42', '22', '11'], 'Gold', []],
            'Public Administration' : [['92'], 'Indigo', []]
        }
    
    ## Make a DataFrame for our 2 character codes
    naics_to_group = {}
    for group_name, code_list in groups.items():
        for code in code_list[0]:
            naics_to_group[code] = group_name
    df_place['NAICS_CODE_FINAL'] = df_place['NAICS_CODE'].astype(str).str[:2].map(lambda x: naics_to_group.get(x, 'Other'))

    ## Getting data and putting it in readable form for the bar graph
    counts_poi = df_place.groupby(['CITY', 'NAICS_CODE_FINAL']).size().unstack(fill_value = 0)
    counts_poi.loc['Cooke City & Silver Gate'] = counts_poi.loc['Cooke City'] + counts_poi.loc['Silver Gate']
    counts_poi = counts_poi.drop(['Cooke City', 'Silver Gate'])

    ## Making final graph
    fig1, ax1 = plt.subplots(figsize = (15, 3))
    x = np.arange(len(counts_poi.index))
    width = 0.8 / len(groups)
    for j, (naics, data) in enumerate(groups.items()):
        values = counts_poi[naics].values
        color = data[1]
        ax1.bar(x + j * width, values, width = width, color = color)
    
    ax1.set_title("Total POIs in Region by NAICS")
    ax1.set_xticks(x + width * (len(groups) - 1) / 2)
    ax1.set_xticklabels(['', '', '', '', '', '']) ## Replace by (textwrap.fill(l, 13) for l in counts_poi.index), rotation=45)
    ax1.set_yscale('log')

    ## Repeat for Spending Data
    df_filtered_spend = time_filt(df_safegraph_spend, start, end)
    if 'PLACEKEY' in df_filtered_spend.columns and 'PLACEKEY' in df_place.columns:
        df_spend = df_place.merge(df_filtered_spend[['PLACEKEY', 'RAW_TOTAL_SPEND']], on='PLACEKEY', how='inner')

        naics_to_group = {}
        for group_name, code_list in groups.items():
            for code in code_list[0]:
                naics_to_group[code] = group_name
        df_spend['NAICS_CODE_FINAL'] = df_spend['NAICS_CODE'].astype(str).str[:2].map(lambda x: naics_to_group.get(x, 'Other'))
        
        ## Getting data and putting it in readable form for the bar graph
        counts_spend = df_spend.groupby(['CITY', 'NAICS_CODE_FINAL'])['RAW_TOTAL_SPEND'].sum().unstack(fill_value = 0)
        counts_spend.loc['Cooke City & Silver Gate'] = counts_spend.loc['Cooke City'] + counts_spend.loc['Silver Gate']
        counts_spend = counts_spend.drop(['Cooke City', 'Silver Gate'])
        counts_spend = counts_spend.reindex(columns=groups.keys(), fill_value=0)

        fig2, ax2 = plt.subplots(figsize = (15, 3))
        x = np.arange(len(counts_spend.index))
        width = 0.8 / len(groups)
        for j, (naics, data) in enumerate(groups.items()):
            values = counts_spend[naics].values
            color = data[1]
            ax2.bar(x + j * width, values, width = width, color = color)
    
        ax2.set_title("Total Spending in Region by NAICS")
        ax2.set_xticks(x + width * (len(groups) - 1) / 2)
        ax2.set_xticklabels((textwrap.fill(l, 13) for l in counts_spend.index), rotation=45)
        ax2.set_yscale('log')
    
    return



def type_stacked_pie(df_safegraph_spend, df_pie, months, prev_months, place, groups):
    plt.rcParams['axes.labelsize'] = 20
    plt.rcParams['xtick.labelsize'] = 20
    plt.rcParams['ytick.labelsize'] = 25
    ## Merging DataFrames so we know which spending belongs to which NAICS category
    fig2, ax3 = plt.subplots(figsize = (15, 8))
    df_total = df_safegraph_spend.merge(df_pie[['PLACEKEY', 'NAICS_CODE_FINAL']], on='PLACEKEY', how='inner')

    ## Setting up Stacked Bar chart things
    for i in range(len(months) - 1):
        df_total_filtered = time_filt(df_total, months[i], months[i+1])
        ## Getting total money value for each NAICS code over each month
        spend_total = df_total_filtered.groupby('NAICS_CODE_FINAL')['RAW_TOTAL_SPEND'].sum().astype(int)
        for group_name, group_data in groups.items():
            flood_money = spend_total.get(group_name, 0)
            group_data[2].append(flood_money)
    
    ## Setting up prev years totals
    df_total_filtered_prev = time_filt(df_total, prev_months[0], prev_months[-1])
    spend_total_prev = df_total_filtered_prev.groupby('SPEND_DATE_RANGE_START')['RAW_TOTAL_SPEND'].sum().astype(int)

    ## Making final graph
    bottom = np.zeros(len(months)-1)
    for naics, data in groups.items():
        values = np.array(data[2])
        ax3.bar(months[:-1], values, bottom = bottom, color = data[1])
        bottom += values
    ax3.plot(months[:-1], spend_total_prev.values, color='black', marker='o')
    ax3.tick_params(axis = 'x', labelrotation = 45)
    ax3.set_xticklabels(['January', 'Feburary', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])
    #ax3.set_xticklabels([])
    ax3.legend()
    ax3.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))

    if type(place) == list:
        title = ''
        for i in place:
            title += i + ', '
        fig2.suptitle('Spending at POIs in ' + title[:-2], fontsize = '24')
    else:
        fig2.suptitle('Spending at POIs in ' + place, fontsize = '24')
        x=1

    return



def total_DS(place, df_safegraph_poi, df_safegraph_spend, before_flood_start, before_flood_end, 
                        during_flood_start, during_flood_end, after_flood_start, after_flood_end):

    ## Setting up DataFrame for specific place and time
    if type(place) == list:
        df_place_poi = df_safegraph_poi[df_safegraph_poi['CITY'].isin(place)]
        place_title = ' and '.join(place)
    else:
        mask = df_safegraph_poi['CITY'] == place                    
        df_place_poi = df_safegraph_poi[mask]
        place_title = place
    if 'PLACEKEY' in df_safegraph_spend.columns:
        df_place = df_safegraph_spend[df_safegraph_spend['PLACEKEY'].isin(df_place_poi['PLACEKEY'])]
    df_place_flood = time_filt(df_place, '2022-05-01', '2022-08-01')
    df_flood_spending = spend_by_day(df_place_flood)
    before_flood = df_flood_spending[33:40]
    during_flood = df_flood_spending[40:47]
    after_flood = df_flood_spending[47:54]

    ## Making graphs for Daily Spending during our timeframe. First graph is week before - week after. Second graph is month before - month after
    plt.rcParams['axes.labelsize'] = 16
    plt.rcParams['xtick.labelsize'] = 20
    plt.rcParams['ytick.labelsize'] = 20
    fig1, ax1 = plt.subplots(figsize = (15, 4))
    ax1.plot(before_flood)
    ax1.plot(during_flood)
    ax1.plot(after_flood)
    ax1.plot([before_flood.index[-1], during_flood.index[0]], [before_flood.values[-1], during_flood.values[0]], color='grey', linestyle='--')
    ax1.plot([during_flood.index[-1], after_flood.index[0]], [during_flood.values[-1], after_flood.values[0]], color='grey', linestyle='--')
    ax1.axvline(x=pd.Timestamp('2022-06-13'), color = 'k', label = 'Flood Start')
    ax1.legend(['Week Before Flood', 'Week of Flood', 'Week After Flood'])
    fig1.suptitle(place_title, fontsize='24');

    df_place_timeframe = time_filt(df_place, before_flood_start, after_flood_end)
    df_spend_timeframe = spend_by_day(df_place_timeframe)

    fig2, ax2 = plt.subplots(figsize=(15, 4));
    ax2.plot(df_spend_timeframe.index, df_spend_timeframe.values)
    ax2.axvline(x=pd.Timestamp('2022-06-13'), color = 'k', label = 'Flood Start')
    ax2.set_xticklabels([])
    ax2.set_xticklabels(['May', '', 'June', '', 'July', '', 'August'])
    ax2.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    ax2.tick_params(axis = 'x', labelrotation = 45)
    ax2.tick_params(axis = 'y', colors='tab:blue')
    ax2.set_ylabel('Dollars Spent in Thousands')
    
    ax3 = ax2.twinx()
    movement_df = pd.read_csv(f'CSV_Movement/{place_title}_Movement.csv').set_index('Date')
    movement_df.columns = movement_df.columns.str.strip()
    movement_df.index = pd.to_datetime(movement_df.index)
    ax3.plot(movement_df.index, movement_df['daily_arrivals'], color='tab:red')
    ax3.tick_params(axis='y', colors='tab:red')
    ax3.set_ylabel('Number of Arrivals')


    ## Setting up dataframes for future use
    df_place_before = time_filt(df_place, before_flood_start, before_flood_end)
    df_place_during = time_filt(df_place, during_flood_start, during_flood_end)
    df_place_after = time_filt(df_place, after_flood_start, after_flood_end)
    df_spend_before = spend_by_day(df_place_before)
    df_spend_during = spend_by_day(df_place_during)
    df_spend_after = spend_by_day(df_place_after)

    ## This code is for graphing seperate time frames if desired
    #fig2, ax2 = plt.subplots(figsize=(15, 4));
    #ax2.plot(df_spend_before)
    #ax2.plot(df_spend_during)
    #ax2.plot(df_spend_after)
    #ax2.plot([df_spend_before.index[-1], df_spend_during.index[0]],[df_spend_before.values[-1], df_spend_during.values[0]],color='gray', linestyle='--')
    #ax2.plot([df_spend_during.index[-1], df_spend_after.index[0]],[df_spend_during.values[-1], df_spend_after.values[0]],color='gray', linestyle='--')
    #ax2.legend(['Month Before (May)', 'Month Of (June)', 'Month After (July)'])
    #fig2.suptitle(place_title, fontsize='24');

    return [[df_place, df_place_before, df_place_during, df_place_after], [df_spend_before, df_spend_during, df_spend_after]]



def total_SOO(df_place_before, df_place_during, df_place_after):
    plt.rcParams['axes.titlesize'] = 20
    ## Pie Charts for what transactions were instate vs out of state
    before = percent_instate(df_place_before)
    during = percent_instate(df_place_during)
    after = percent_instate(df_place_after)

    ## Setting up Color Map for Pie Charts
    i = 0
    states = [ 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    custom_map = {
        'WY' : 'Gold',
        'MT' : 'Lightcoral',
        'SD' : 'Cyan',
        'CO' : 'Springgreen',
        'ID' : 'Darkviolet'
    }
    cmap = cm.get_cmap('Set3', len(states))
    color_map = {
        'Other' : 'RoyalBlue'
    }
    for state in states:
        if state in custom_map:
            color_map[state] = custom_map[state]
        else:
            color_map[state] = cmap(i)
            i += 1

    before_total = 0
    during_total = 0
    after_total = 0
    for i in before[1]:
        before_total += i[1]
    for j in during[1]:
        during_total += j[1]
    for k in after[1]:
        after_total += k[1]


    ## Add labels=[label[0] for label in (before, during, after)[1]] and autopct='%1.1f%%' for a specific numbers on pie chart
    fig, axs = plt.subplots(1, 3, figsize=(15, 5));
    ax1, ax2, ax3 = axs.flatten()
    ax1.pie([data[1] for data in before[1]], colors=[color_map[label[0]] for label in before[1]]);
    ax1.set_title('Before flood (May)');
    ax2.pie([data[1] for data in during[1]], colors=[color_map[label[0]] for label in during[1]]);
    ax2.set_title('During flood (June)');
    ax3.pie([data[1] for data in after[1]], colors=[color_map[label[0]] for label in after[1]]);
    ax3.set_title('After flood (July)');
    
    ## This code is for graphing SOO by largest state rather than closest. Add ax4, ax5, ax6 to axs.flatten() and change fig to plot 2x3 subplots
    #ax4.pie([data[1] for data in before[0]], labels=[label[0] for label in before[0]], colors = [color_map[label[0]] for label in before[0]], autopct='%1.1f%%')
    #ax5.pie([data[1] for data in during[0]], labels=[label[0] for label in during[0]], colors = [color_map[label[0]] for label in during[0]], autopct='%1.1f%%')
    #ax6.pie([data[1] for data in after[0]], labels=[label[0] for label in after[0]], colors = [color_map[label[0]] for label in after[0]], autopct='%1.1f%%')

    return [before, during, after]



def total_CSV(df_place, before_flood_start, after_flood_end, before, during, after, place):
    ## Making CSV for Spending Info
    df_place_full = time_filt(df_place, before_flood_start, after_flood_end)
    flood_df = {}
    for i in before[2]:
        state = i[0]
        before_total = i[1]
        flood_df[state] = [before_total, 0, 0]
    for j in during[2]:
        state = j[0]
        during_total = j[1]
        if state not in flood_df:
            flood_df[state] = [0, during_total, 0]
        else:
            flood_df[state][1] = during_total
    for k in after[2]:
        state = k[0]
        after_total = k[1]
        if state not in flood_df:
            flood_df[state] = [0, 0, after_total]
        else:
            flood_df[state][2] = after_total
    flood_df = pd.DataFrame(flood_df, index = ['Before Flood State of Orign Totals', 'During Flood State of Orign Totals', 'After Flood State of Orign Totals']).transpose()
    if type(place) == list:
        name = "".join(place) + '_Spend.csv'
    else:
        name = place + '_Spend.csv'
    ## Uncomment for output to csv
    #df_place_full.to_csv(name)


## This code graphs additional graphs based on spending by specific type of NAICS code
def show_data_TOS(place, df_safegraph_poi, df_safegraph_spend, before_flood_start, before_flood_end, 
                during_flood_start, during_flood_end, after_flood_start, after_flood_end, month, 
                naics, TOS):
    ## Setting up dataframe for our graphs
    mask = df_safegraph_poi['CITY'] == place
    df_place_TOS = df_safegraph_poi[mask]
    combined_mask = np.zeros(len(df_place_TOS),dtype=bool)
    if type(naics) == list:
        for i in naics:
            mask = [ str(ncode)[:3]==i for ncode in list(df_place_TOS['NAICS_CODE']) ]
            combined_mask += mask
        df_TOS = df_place_TOS[combined_mask]
    else:
        mask = [ str(ncode)[:3]==naics for ncode in list(df_place_TOS['NAICS_CODE']) ]
        df_TOS = df_place_TOS[mask]
    if 'PLACEKEY' in df_safegraph_spend.columns:
        df_place_TOS = df_safegraph_spend[df_safegraph_spend['PLACEKEY'].isin(df_TOS['PLACEKEY'])]

    df_TOS_before = time_filt(df_place_TOS, before_flood_start, before_flood_end)
    df_TOS_during = time_filt(df_place_TOS, during_flood_start, during_flood_end)
    df_TOS_after = time_filt(df_place_TOS, after_flood_start, after_flood_end)
   
    ## Graphs for Total Daily Spending of TOS. First is timeframe from week before flood-week after. Second is month before-month after
    df_thing_flood = time_filt(df_place_TOS, before_flood_start, after_flood_end)
    df_flood_spending_TOS = spend_by_day(df_thing_flood)

    before_flood_TOS = df_flood_spending_TOS[33:40]
    during_flood_TOS = df_flood_spending_TOS[40:47]
    after_flood_TOS = df_flood_spending_TOS[47:54]

    fig1, ax1 = plt.subplots(figsize=(15, 4), sharex = True);
    ax1.plot(before_flood_TOS)
    ax1.plot(during_flood_TOS)
    ax1.plot(after_flood_TOS)
    ax1.legend(['Week Before Flood', 'Week During Flood', 'Week After Flood'])
    fig1.suptitle('Daily Spending: ' + TOS + ', ' + place, fontsize='24');

    df_spend_before_TOS = spend_by_day(df_TOS_before)
    df_spend_during_TOS = spend_by_day(df_TOS_during)
    df_spend_after_TOS = spend_by_day(df_TOS_after)

    fig2, ax2 = plt.subplots(figsize=(15, 4));
    ax2.plot(df_spend_before_TOS)
    ax2.plot(df_spend_during_TOS)
    ax2.plot(df_spend_after_TOS)
    ax2.legend(['Month Before (May)', 'Month During (June)', 'Month After (July)'])
    fig2.suptitle('Daily Spending: ' + TOS, fontsize='24');

    ## Pie Charts for what transactions were instate vs out of state
    before = percent_instate(df_TOS_before)
    during = percent_instate(df_TOS_during)
    after = percent_instate(df_TOS_after)

    ## Pie Chart Color mapping
    color_map = {
        'WY' : 'Gold',
        'CO' : 'Springgreen',
        'MT' : 'Lightcoral',
        'ID' : 'Purple',
        'SD' : 'Aqua',
        'Other' : 'RoyalBlue'
    }

    before_total = 0
    during_total = 0
    after_total = 0
    for i in before[1]:
        before_total += i[1]
    for j in during[1]:
        during_total += j[1]
    for k in after[1]:
        after_total += k[1]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 6));
    ax1.pie([data[1] for data in before[1]], labels=[label[0] for label in before[1]], colors=[color_map[label[0]] for label in before[1]], autopct='%1.1f%%');
    ax1.set_title('Before flood (May), Total Sales: ' + str(before_total));
    ax2.pie([data[1] for data in during[1]], labels=[label[0] for label in during[1]], colors=[color_map[label[0]] for label in during[1]], autopct='%1.1f%%');
    ax2.set_title('During flood (June), Total Sales: ' + str(during_total));
    ax3.pie([data[1] for data in after[1]], labels=[label[0] for label in after[1]], colors=[color_map[label[0]] for label in after[1]], autopct='%1.1f%%');
    ax3.set_title('After flood (July), Total Sales: ' + str(after_total));
    fig.suptitle('State of Origin: ' + TOS, fontsize='24');

    ## Making map for monthly spending at place
    df_TOS_jan = time_filt(df_place_TOS, month[0], month[1])
    df_TOS_feb = time_filt(df_place_TOS, month[1], month[2])
    df_TOS_mar = time_filt(df_place_TOS, month[2], month[3])
    df_TOS_apr = time_filt(df_place_TOS, month[3], month[4])
    df_TOS_may = time_filt(df_place_TOS, month[4], month[5])
    df_TOS_jun = time_filt(df_place_TOS, month[5], month[6])
    df_TOS_jul = time_filt(df_place_TOS, month[6], month[7])
    df_TOS_aug = time_filt(df_place_TOS, month[7], month[8])
    df_TOS_sep = time_filt(df_place_TOS, month[8], month[9])
    df_TOS_oct = time_filt(df_place_TOS, month[9], month[10])
    df_TOS_nov = time_filt(df_place_TOS, month[10], month[11])
    df_TOS_dec = time_filt(df_place_TOS, month[11], month[12])
    TOS_dfs = [df_TOS_jan, df_TOS_feb, df_TOS_mar, df_TOS_apr, df_TOS_may, df_TOS_jun, 
             df_TOS_jul, df_TOS_aug, df_TOS_sep, df_TOS_oct, df_TOS_nov, df_TOS_dec]
    
    ## Graph for percent change of spending compared to year prior
    prev_year_pct=[]
    for i in range(0, len(TOS_dfs)):
        prev_year_pct.append(percent_change_year(TOS_dfs[i]))
    fig, ax = plt.subplots(figsize=(15, 4))
    ax.plot(month[0:12], prev_year_pct);
    ax.set_title('Percent Change compared to 2021: ' + TOS);
    ax.set_xlabel('Date');
    ax.set_ylabel('Percent Change');

    ## Graph for percent change of spending compared to month prior
    prev_month_pct=[]
    for i in range(0, len(TOS_dfs)):
        prev_month_pct.append(percent_change_month(TOS_dfs[i]))
    fig, ax = plt.subplots(figsize=(15, 4))
    ax.plot(month[0:12], prev_month_pct);
    ax.set_title('Percent Change compared to prior month: ' + TOS);
    ax.set_xlabel('Date');
    ax.set_ylabel('Percent Change');
    
    return [before_flood_TOS, during_flood_TOS, after_flood_TOS]