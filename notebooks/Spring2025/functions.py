import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.cm as cm
import pandas as pd
import geopandas as gpd
import plotly.express as px
import numpy as np
import ast

def map_points(fig,df):
    gdf_safegraph_poi = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LONGITUDE, df.LATITUDE))
    fig = px.scatter_mapbox(
        gdf_safegraph_poi,
        lat='LATITUDE',
        lon='LONGITUDE',
        hover_name="LOCATION_NAME",
        hover_data=["CITY"],
        zoom=6,
        opacity=0.5)
  
    return fig



def get_data_accom_region(df_safegraph_poi, df_safegraph_spend, TOS_naics, start, end):
    mask = [ str(ncode)[:3]==TOS_naics for ncode in list(df_safegraph_poi['NAICS_CODE']) ]
    df_TOS = df_safegraph_poi[mask]

    if 'PLACEKEY' in df_safegraph_spend.columns:
        df_filtered = df_safegraph_spend[df_safegraph_spend['PLACEKEY'].isin(df_TOS['PLACEKEY'])]
    else:
        print("Error: DataFrame does not contain 'PLACEKEY' column.")

    fig = plt.figure()
    fig = map_points(fig,df_TOS)
    fig.update_layout(title="Accomodations in Greater Yellowstone Region",height=800,width=1200,mapbox_style="open-street-map")
    fig.show()

    tos = 'accom'
    grouped_22_lodging = make_graph_year_TOS(df_filtered, start, end, tos)
    grouped_22_lodging = px.line(grouped_22_lodging)
    grouped_22_lodging.show()
    return



def get_data_food_region(df_safegraph_poi, df_safegraph_spend, naics, 
                         start_1, end_1, start_2, end_2, start_3, end_3, start_4, end_4):
    mask = [ str(ncode)[:4]==naics for ncode in list(df_safegraph_poi['NAICS_CODE']) ]
    df_food = df_safegraph_poi[mask]

    if 'PLACEKEY' in df_safegraph_spend.columns:
        df_filtered = df_safegraph_spend[df_safegraph_spend['PLACEKEY'].isin(df_food['PLACEKEY'])]
    else:
        print("Error: DataFrame does not contain 'PLACEKEY' column.")

    fig = plt.figure()
    fig = map_points(fig,df_food)
    fig.update_layout(title="Food in Greater Yellowstone Region",height=800,width=1200,mapbox_style="open-street-map")
    fig.show()

    tos = 'food'
    df_19 = df_filtered.copy()
    df_20 = df_filtered.copy()
    df_21 = df_filtered.copy()
    df_22 = df_filtered.copy()
    grouped_19_food = make_graph_year_TOS(df_19, start_1, end_1, tos)
    grouped_20_food = make_graph_year_TOS(df_20, start_2, end_2, tos)
    grouped_21_food = make_graph_year_TOS(df_21, start_3, end_3, tos)
    grouped_22_food = make_graph_year_TOS(df_22, start_4, end_4, tos)

    plt.figure(figsize=(20, 8))
    plt.plot(grouped_19_food);
    plt.plot(grouped_20_food);
    plt.plot(grouped_21_food);
    plt.plot(grouped_22_food);
    plt.title('Spending per Day, Food');
    plt.xlabel('day');
    plt.ylabel('$');
    plt.xticks(rotation=45)
    plt.legend(['2019', '2020', '2021', '2022']);
    return



def make_graph_year_TOS(df_filtered, start, end, tos):
    
    df = df_filtered.copy()

    df_filtered['SPEND_DATE_RANGE_START'] = pd.to_datetime(df_filtered['SPEND_DATE_RANGE_START'])
    df_filtered['SPEND_DATE_RANGE_END'] = pd.to_datetime(df_filtered['SPEND_DATE_RANGE_END'])

    df_year = df[(df_filtered['SPEND_DATE_RANGE_START'] >= start) & (df_filtered['SPEND_DATE_RANGE_END'] <= end)]

    df = df_year.copy()

    # Convert string representations of lists in 'SPEND_BY_DAY' to actual lists
    df['SPEND_BY_DAY'] = df['SPEND_BY_DAY'].apply(ast.literal_eval)

    # Add a new column called 'DATE_OF_MONTH', as a list of integers from 1 to the end of the month (length of the 'SPEND_BY_DAY' list)
    df['DATE_OF_MONTH'] = df['SPEND_BY_DAY'].apply(lambda x: list(range(1, len(x) + 1)))

    df_spend_by_day = df.explode(['SPEND_BY_DAY', 'DATE_OF_MONTH'])

    df_spend_by_day['SPEND_BY_DAY'] = df_spend_by_day['SPEND_BY_DAY'].astype(float)
    df_spend_by_day['DATE_OF_MONTH'] = df_spend_by_day['DATE_OF_MONTH'].astype(int)

    df_spend_by_day['DATE'] = pd.to_datetime(df_spend_by_day['SPEND_DATE_RANGE_START']) + pd.to_timedelta(df_spend_by_day['DATE_OF_MONTH'] - 1, unit='D')
    if tos == 'food':
        df_spend_by_day['DATE'] = df_spend_by_day['DATE'].dt.strftime('%m-%d')

    grouped_year_TOS = df_spend_by_day.groupby('DATE')['SPEND_BY_DAY'].sum()
    return grouped_year_TOS



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



def type_pie_town(df_safegraph_poi, df_safegraph_spend, place, months, prev_months):
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

    print("Here is unfiltered number of POIs", len(df_place))

    ## Make a DataFrame for our 2 character codes
    naics_to_group = {}
    for group_name, code_list in groups.items():
        for code in code_list[0]:
            naics_to_group[code] = group_name

    ## Getting data and putting it in readable form for the pie chart
    df_place['NAICS_CODE_FINAL'] = df_place['NAICS_CODE'].astype(str).str[:2].map(lambda x: naics_to_group.get(x, 'Dump'))
    naics_codes = df_place['NAICS_CODE_FINAL'].value_counts()

    ## Making the pie chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    ax1.pie(naics_codes, colors = [groups[label][1] for label in naics_codes.index])
    fig.legend()
    if type(place) == list:
            #title = ''
            #for i in place:
            #    title += i + ', '
            ax1.set_title('Total POIs')
    else:
        ax1.set_title('POIs in ' + place)
    #fig.legend(naics_codes.index, fontsize = 'small')

    ## Repeat process for specific POIs that had credit card spending at them
    if 'PLACEKEY' in df_safegraph_spend.columns and 'PLACEKEY' in df_place.columns:
        df_pie = df_place[df_place['PLACEKEY'].isin(df_safegraph_spend['PLACEKEY'])]

        print("Here is the total POIS", len(df_pie))

        naics_to_group = {}
        for group_name, code_list in groups.items():
            for code in code_list[0]:
                naics_to_group[code] = group_name

        df_pie['NAICS_CODE_FINAL'] = df_pie['NAICS_CODE'].astype(str).str[:2].map(lambda x: naics_to_group.get(x, 'Other'))
        naics_codes_filtered = df_pie['NAICS_CODE_FINAL'].value_counts()
        
        ax2.pie(naics_codes_filtered, colors = [groups[label][1] for label in naics_codes_filtered.index])
        if type(place) == list:
            title = ''
            for i in place:
                title += i + ', '
            ax2.set_title('POIs with spending')
        else:
            ax2.set_title('POIs with spending in ' + place)

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
    ax3.plot(months[:-1], spend_total_prev.values, color='black', marker='o', label='Previous Year Total')
    ax3.tick_params(axis = 'x', labelrotation = 45)
    ax3.set_xticklabels(['January', 'Feburary', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])
    ax3.legend()
    ax3.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    ax3.set_ylabel('Dollars Spent in Thousands')

    if type(place) == list:
        title = ''
        for i in place:
            title += i + ', '
        fig2.suptitle('Spending at POIs in ' + title[:-2], fontsize = '24')
    else:
        fig2.suptitle('Spending at POIs in ' + place, fontsize = '24')
        x=1

    return



def show_data_TOS_total(place, df_safegraph_poi, df_safegraph_spend, before_flood_start, before_flood_end, 
                        during_flood_start, during_flood_end, after_flood_start, after_flood_end, month):
    
    ## Setting up DataFrame for specific place and time
    if type(place) == list:
        df_place_poi = df_safegraph_poi[df_safegraph_poi['CITY'].isin(place)]
        place_title = ', '.join(place)
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

    ## Making graphs for Daily Spending during our timeframe. First graph is week before-week after. Second graph is month before-month after
    fig1, ax1 = plt.subplots(figsize = (15, 4))
    ax1.plot(before_flood)
    ax1.plot(during_flood)
    ax1.plot(after_flood)
    ax1.legend(['Week Before Flood', 'Week of Flood', 'Week After Flood'])
    fig1.suptitle('Daily Spending: ' + place_title, fontsize='24');

    df_place_before = time_filt(df_place, before_flood_start, before_flood_end)
    df_place_during = time_filt(df_place, during_flood_start, during_flood_end)
    df_place_after = time_filt(df_place, after_flood_start, after_flood_end)
    df_spend_before = spend_by_day(df_place_before)
    df_spend_during = spend_by_day(df_place_during)
    df_spend_after = spend_by_day(df_place_after)

    fig2, ax2 = plt.subplots(figsize=(15, 4));
    ax2.plot(df_spend_before)
    ax2.plot(df_spend_during)
    ax2.plot(df_spend_after)
    ax2.legend(['Month Before (May)', 'Month Of (June)', 'Month After (July)'])
    fig2.suptitle('Daily Spending: ' + place_title, fontsize='24');

    ## Pie Charts for what transactions were instate vs out of state
    before = percent_instate(df_place_before)
    during = percent_instate(df_place_during)
    after = percent_instate(df_place_after)

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
    #df_place_full.to_csv(name)

    ## Setting up Color Map for Pie Charts
    i = 0
    states = [ 'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    custom_map = {
        'WY' : 'Gold'
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

    fig, axs = plt.subplots(2, 3, figsize=(15, 6));
    ax1, ax2, ax3, ax4, ax5, ax6 = axs.flatten()
    ax1.pie([data[1] for data in before[1]], labels=[label[0] for label in before[1]], colors=[color_map[label[0]] for label in before[1]], autopct='%1.1f%%');
    ax1.set_title('Before flood (May), Total Sales: ' + str(before_total));
    ax2.pie([data[1] for data in during[1]], labels=[label[0] for label in during[1]], colors=[color_map[label[0]] for label in during[1]], autopct='%1.1f%%');
    ax2.set_title('During flood (June), Total Sales: ' + str(during_total));
    ax3.pie([data[1] for data in after[1]], labels=[label[0] for label in after[1]], colors=[color_map[label[0]] for label in after[1]], autopct='%1.1f%%');
    ax3.set_title('After flood (July), Total Sales: ' + str(after_total));
    ax4.pie([data[1] for data in before[0]], labels=[label[0]for label in before[0]], colors = [color_map[label[0]] for label in before[0]], autopct='%1.1f%%')
    ax5.pie([data[1] for data in during[0]], labels=[label[0]for label in during[0]], colors = [color_map[label[0]] for label in during[0]], autopct='%1.1f%%')
    ax6.pie([data[1] for data in after[0]], labels=[label[0]for label in after[0]], colors = [color_map[label[0]] for label in after[0]], autopct='%1.1f%%')
    fig.suptitle('State of Origin: All Transactions' , fontsize='24');

    ## Making map for monthly spending at place
    df_place_jan = time_filt(df_place, month[0], month[1])
    df_place_feb = time_filt(df_place, month[1], month[2])
    df_place_mar = time_filt(df_place, month[2], month[3])
    df_place_apr = time_filt(df_place, month[3], month[4])
    df_place_may = time_filt(df_place, month[4], month[5])
    df_place_jun = time_filt(df_place, month[5], month[6])
    df_place_jul = time_filt(df_place, month[6], month[7])
    df_place_aug = time_filt(df_place, month[7], month[8])
    df_place_sep = time_filt(df_place, month[8], month[9])
    df_place_oct = time_filt(df_place, month[9], month[10])
    df_place_nov = time_filt(df_place, month[10], month[11])
    df_place_dec = time_filt(df_place, month[11], month[12])
    month_dfs = [df_place_jan, df_place_feb, df_place_mar, df_place_apr, df_place_may, df_place_jun, 
             df_place_jul, df_place_aug, df_place_sep, df_place_oct, df_place_nov, df_place_dec]

    ## Graph for percent change of spending compared to year prior
    prev_year_pct=[]
    for i in range(0, len(month_dfs)):
        prev_year_pct.append(percent_change_year(month_dfs[i]))
    fig, ax = plt.subplots(figsize=(15, 4))
    ax.plot(month[0:12], prev_year_pct);
    ax.set_title('Percent Change compared to 2021');
    ax.set_xlabel('Date');
    ax.set_ylabel('Percent Change');

    ## Graph for percent change of spending compared to month prior
    prev_month_pct=[]
    for i in range(0, len(month_dfs)):
        prev_month_pct.append(percent_change_month(month_dfs[i]))
    fig, ax = plt.subplots(figsize=(15, 4))
    ax.plot(month[0:12], prev_month_pct);
    ax.set_title('Percent Change compared to prior month');
    ax.set_xlabel('Date');
    ax.set_ylabel('Percent Change');

    return [before_flood, during_flood, after_flood]



def show_data_TOS(place, df_safegraph_poi, df_safegraph_spend, df_movement, before_flood_start, before_flood_end, 
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

def aggregate(flood, flood_accom, flood_food, flood_retail, flood_transit, place):
    ## Making Aggregate for each type of spending interested in and total spending
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharey=True);
    ax1.plot(flood[0], label='Total Daily Spending')
    ax1.plot(flood_accom[0], label='Accomodation Daily Spending');
    ax1.plot(flood_food[0], label='Food Daily Spending')
    ax1.plot(flood_retail[0], label='Retail Daily Spending')
    ax1.plot(flood_transit[0], label='Transit Daily Spending')
    ax1.set_title('Week before flood');
    ax2.plot(flood[1])
    ax2.plot(flood_accom[1])
    ax2.plot(flood_food[1])
    ax2.plot(flood_retail[1])
    ax2.plot(flood_transit[1])
    ax2.set_title('Week of flood');
    ax3.plot(flood[2])
    ax3.plot(flood_accom[2])
    ax3.plot(flood_food[2])
    ax3.plot(flood_retail[2])
    ax3.plot(flood_transit[2])
    ax3.set_title('Week after flood');
    fig.suptitle('Daily Spending: ' + place, fontsize='24');
    fig.legend();
    return
