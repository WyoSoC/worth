import os
import matplotlib.pyplot as plt
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
    in_state = 0
    out_state = 0

    for val in home_city:
        cities = val.split(",")
        cities = cities[1::2]
        for i in cities:
            state = i.split(':')
            if(state[0].find("WY") != 1):
                count = state[1].strip("{}")
                out_state += int(count)
            else:
                count = state[1].strip("{}")
                in_state += int(count)
    
    #print('Out of state: ', out_state)
    #print('In state: ', in_state)
    #print('Percentage out of state:', (out_state)/(in_state+out_state)*100, '%')
    
    return [in_state, out_state]



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

    print('\n')

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
            'Agriculture' : ['11'],
            'Construction' : ['23'],
            'Manufacturing' : ['31', '32', '33'],
            'Retail' : ['44', '45'],
            'Transportation' : ['48', '49'],
            'Real Estate' : ['53'],
            'Technical Services' : ['54'],
            'Administrative Services' : ['56'],
            'Health Care' : ['62'],
            'Arts' : ['71'],
            'Accomodations and Food' : ['72'],
            'Other' : ['81', '55', '21', '52', '61', '51', '42', '22'],
            'Public Administration' : ['91']
        }

    #print("Here is unfiltered number of POIs", len(df_place))

    ## Make a DataFrame for our 2 character codes
    naics_to_group = {}
    for group_name, code_list in groups.items():
        for code in code_list:
            naics_to_group[code] = group_name

    ## Getting data and putting it in readable form for the pie chart
    df_place['NAICS_CODE_FINAL'] = df_place['NAICS_CODE'].astype(str).str[:2].map(lambda x: naics_to_group.get(x, 'Dump'))
    naics_codes = df_place['NAICS_CODE_FINAL'].value_counts()

    ## Making the pie chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 12), sharey=True)
    ax1.pie(naics_codes, labels = naics_codes.index)
    if type(place) == list:
            title = ''
            for i in place:
                title += i + ', '
            ax1.set_title('POIs with spending in ' + title)
    else:
        ax1.set_title('POIs with spending in ' + place)


    ## Repeat process for specific POIs that had credit card spending at them  (Check with team about specifics)
    if 'PLACEKEY' in df_safegraph_spend.columns and 'PLACEKEY' in df_place.columns:
        df_pie = df_place[df_place['PLACEKEY'].isin(df_safegraph_spend['PLACEKEY'])]

        print("Here is the total POIS", len(df_pie))

        naics_to_group = {}
        for group_name, code_list in groups.items():
            for code in code_list:
                naics_to_group[code] = group_name

        df_pie['NAICS_CODE_FINAL'] = df_pie['NAICS_CODE'].astype(str).str[:2].map(lambda x: naics_to_group.get(x, 'Other'))
        naics_codes_filtered = df_pie['NAICS_CODE_FINAL'].value_counts()
        
        ax2.pie(naics_codes_filtered, labels=naics_codes_filtered.index)
        if type(place) == list:
            title = ''
            for i in place:
                title += i + ', '
            ax2.set_title('POIs with spending in ' + title)
        else:
            ax2.set_title('POIs with spending in ' + place)
    fig.suptitle("POIs")

    return



def show_data_TOS_total(place, df_safegraph_poi, df_safegraph_spend, before_flood_start, before_flood_end, 
                        during_flood_start, during_flood_end, after_flood_start, after_flood_end, month):
    
    ## Setting up DataFrame for specific place and time
    mask = df_safegraph_poi['CITY'] == place                    
    df_place_poi = df_safegraph_poi[mask]
    if 'PLACEKEY' in df_safegraph_spend.columns:
        df_place = df_safegraph_spend[df_safegraph_spend['PLACEKEY'].isin(df_place_poi['PLACEKEY'])]
    df_place_flood = time_filt(df_place, '2022-05-01', '2022-08-01')
    df_flood_spending = spend_by_day(df_place_flood)
    before_flood = df_flood_spending[33:40]
    during_flood = df_flood_spending[40:47]
    after_flood = df_flood_spending[47:54]

    ## Making graph for Daily Spending during our timeframe
    fig, ax = plt.subplots()
    ax.plot(before_flood)
    ax.plot(during_flood)
    ax.plot(after_flood)
    ax.legend(['Week Before Flood', 'Week During Flood', 'Week After Flood'])
    fig.suptitle('Daily Spending: ' + place, fontsize='24');


    df_place_before = time_filt(df_place, before_flood_start, before_flood_end)
    df_place_during = time_filt(df_place, during_flood_start, during_flood_end)
    df_place_after = time_filt(df_place, after_flood_start, after_flood_end)

    df_spend_before = spend_by_day(df_place_before)
    df_spend_during = spend_by_day(df_place_during)
    df_spend_after = spend_by_day(df_place_after)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharey=True);
    ax1.plot(df_spend_before)
    ax1.set_title('Before flood (May)');
    ax2.plot(df_spend_during)
    ax2.set_title('During flood (June)');
    ax3.plot(df_spend_after)
    ax3.set_title('After flood (July)');
    fig.suptitle('Daily Spending, All Transactions', fontsize='24');

    #print('Percent Change April to May: ')
    #print(percent_change_month(df_place_before), '%\n')

    #print('Percent Change May to Jume: ')
    #print(percent_change_month(df_place_during), '%\n')

    #print('Percent Change June to July: ')
    #print(percent_change_month(df_place_after), '%\n')

    #print('Percent Change May 2021 to May 2022: ')
    #print(percent_change_year(df_place_before), '%\n')

    #print('Percent Change June 2021 to Jume 2022: ')
    #print(percent_change_year(df_place_during), '%\n')

    #print('Percent Change July 2021 to July 2022: ')
    #print(percent_change_year(df_place_after), '%\n')

    #print('Before Flooding: ')
    before = percent_instate(df_place_before)
    #print('\n')

    #print('During Flooding: ')
    during = percent_instate(df_place_during)
    #print('\n')

    #print('After Flooding: ')
    after = percent_instate(df_place_after)
    #print('\n')

    labels = 'In State','Out-of-State'
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 6));
    ax1.pie(before, labels=labels, autopct='%1.1f%%');
    ax1.set_title('Before flood (May)');
    ax2.pie(during, labels=labels, autopct='%1.1f%%');
    ax2.set_title('During flood (June)');
    ax3.pie(after, labels=labels, autopct='%1.1f%%');
    ax3.set_title('After flood (July)');
    fig.suptitle('State of Origin, All Transactions', fontsize='24');

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
    
    prev_year_pct=[]

    for i in range(0, len(month_dfs)):
        prev_year_pct.append(percent_change_year(month_dfs[i]))

    fig, ax = plt.subplots(figsize=(16, 5))
    ax.plot(month[0:12], prev_year_pct);
    ax.set_title('Percent Change compared to 2021');
    ax.set_xlabel('Date');
    ax.set_ylabel('Percent Change');

    prev_month_pct=[]

    for i in range(0, len(month_dfs)):
        prev_month_pct.append(percent_change_month(month_dfs[i]))

    fig, ax = plt.subplots(figsize=(16, 5))
    ax.plot(month[0:12], prev_month_pct);
    ax.set_title('Percent Change compared to prior month');
    ax.set_xlabel('Date');
    ax.set_ylabel('Percent Change');

    return [before_flood, during_flood, after_flood]



def show_data_TOS(place, df_safegraph_poi, df_safegraph_spend, before_flood_start, before_flood_end, 
                during_flood_start, during_flood_end, after_flood_start, after_flood_end, month, 
                naics, TOS):
    ## make mask for POI
    mask = df_safegraph_poi['CITY'] == place
    df_place_TOS = df_safegraph_poi[mask]
    combined_mask = np.zeros(len(df_place_TOS),dtype=bool)

    ## make mask for type of spending interested in (TOS)
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
    #print(df_TOS_before.head(5), '\n')

    df_TOS_during = time_filt(df_place_TOS, during_flood_start, during_flood_end)
    #print(df_TOS_during.head(5), '\n')

    df_TOS_after = time_filt(df_place_TOS, after_flood_start, after_flood_end)
    #print(df_TOS_after.head(5), '\n')
    
    ## plot for total daily spending of TOS
    df_thing_flood = time_filt(df_place_TOS, before_flood_start, after_flood_end)
    df_flood_spending_TOS = spend_by_day(df_thing_flood)

    before_flood_TOS = df_flood_spending_TOS[33:40]
    during_flood_TOS = df_flood_spending_TOS[40:47]
    after_flood_TOS = df_flood_spending_TOS[47:54]
    #print(before_flood_TOS)
    #print(during_flood_TOS)
    #print(after_flood_TOS)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharey=True);
    ax1.plot(before_flood_TOS)
    ax1.set_title('Week before flood');
    ax2.plot(during_flood_TOS)
    ax2.set_title('Week of flood');
    ax3.plot(after_flood_TOS)
    ax3.set_title('Week after flood');
    fig.suptitle('Daily Spending: ' + TOS + ', ' + place, fontsize='24');


    df_spend_before_TOS = spend_by_day(df_TOS_before)
    df_spend_during_TOS = spend_by_day(df_TOS_during)
    df_spend_after_TOS = spend_by_day(df_TOS_after)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 11), sharey=True);
    ax1.plot(df_spend_before_TOS)
    ax1.set_title('Before flood (May)');
    ax2.plot(df_spend_during_TOS)
    ax2.set_title('During flood (June)');
    ax3.plot(df_spend_after_TOS)
    ax3.set_title('After flood (July)');

    fig.suptitle('Daily Spending: ' + TOS, fontsize='24');


    #print('Before Flooding: ')
    before = percent_instate(df_TOS_before)
    #print('\n')

    #print('During Flooding: ')
    during = percent_instate(df_TOS_during)
    #print('\n')

    #print('After Flooding: ')
    after = percent_instate(df_TOS_after)
    #print('\n')

    labels = 'In State','Out-of-State'
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 6));

    ax1.pie(before, labels=labels, autopct='%1.1f%%');
    ax1.set_title('Before flood (May)');
    ax2.pie(during, labels=labels, autopct='%1.1f%%');
    ax2.set_title('During flood (June)');
    ax3.pie(after, labels=labels, autopct='%1.1f%%');
    ax3.set_title('After flood (July)');
    fig.suptitle('State of Origin: ' + TOS, fontsize='24');


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
    

    prev_year_pct=[]

    for i in range(0, len(TOS_dfs)):
        prev_year_pct.append(percent_change_year(TOS_dfs[i]))

    fig, ax = plt.subplots(figsize=(16, 5))
    ax.plot(month[0:12], prev_year_pct);
    ax.set_title('Percent Change compared to 2021: ' + TOS);
    ax.set_xlabel('Date');
    ax.set_ylabel('Percent Change');


    prev_month_pct=[]

    for i in range(0, len(TOS_dfs)):
        prev_month_pct.append(percent_change_month(TOS_dfs[i]))

    fig, ax = plt.subplots(figsize=(16, 5))
    ax.plot(month[0:12], prev_month_pct);
    ax.set_title('Percent Change compared to prior month: ' + TOS);
    ax.set_xlabel('Date');
    ax.set_ylabel('Percent Change');
    
    return [before_flood_TOS, during_flood_TOS, after_flood_TOS]

def aggregate(flood, flood_accom, flood_food, flood_retail, flood_transit, place):

    print("===============================")
    print("AGGREGATE")
    print("===============================")

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