import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st


def main():
    st.title("SafeGraph POI Visualization")

    # Load regional POI from saved CSV file
    df_safegraph_poi = pd.read_csv('dewey_data_filtered/SafeGraph_POI_Yellowstone_200miRadius.csv.gz')

    # Convert the DataFrame to a GeoDataFrame
    gdf_safegraph_poi = gpd.GeoDataFrame(
        df_safegraph_poi,
        geometry=gpd.points_from_xy(df_safegraph_poi.LONGITUDE, df_safegraph_poi.LATITUDE),
    )

    # Plot the GeoDataFrame with both scatter points and density map overlay
    fig = px.scatter_mapbox(
        gdf_safegraph_poi,
        lat='LATITUDE',
        lon='LONGITUDE',
        hover_name="LOCATION_NAME",
        hover_data=["CITY"],
        zoom=6,
        opacity=0.5,
    )

    # Add density map overlay
    # fig.add_trace(px.density_mapbox(gdf_safegraph_poi, lat='LATITUDE', lon='LONGITUDE', radius=5, opacity=0.5,).data[0])

    fig.update_layout(
        title="SafeGraph POI in Wyoming",
        height=800,
        width=1200,
        mapbox_style="open-street-map",
    )

    # Display the plot using Streamlit
    st.plotly_chart(fig)


if __name__ == "__main__":
    main()
