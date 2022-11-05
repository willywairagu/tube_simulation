import streamlit as st
import time
import pandas as pd
import base64
from urllib.error import URLError
from datetime import datetime
from tqdm import tqdm_notebook
from itertools import product

# Stats packages
from statsmodels.tsa.statespace.sarimax import SARIMAX

st.set_page_config(page_title="Time series Plotting", page_icon="📈")

# # background image
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"jpg"};base64,{encoded_string.decode()});
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

add_bg_from_local('faint_bg.jpg')


st.markdown("# Time series plotting per station")
st.sidebar.header("Plotting Demo")
st.write(
    """This section illustrates a combination of time series plotting for each station and animation That would aid illustrate
    traffic in this stations over time.."""
)

# reading entry data for modelling
df = pd.read_parquet('Forecasting_Data/data/data.parquet')
format = '%Y-%m'
date_time = []
for i in df.reset_index()['Month-Year']:
    date_time.append(datetime.strptime(i, format))
df['timestamp'] = date_time
df = df.set_index('timestamp')


# prediction function
def sarimax(parameters_list, d, D, s, exog):
    results = []
    for param in tqdm_notebook(parameters_list):
        try:
            model = SARIMAX(exog,
                            order=(param[0], d, param[1]),
                            seasonal_order=(param[2], D, param[3], s)).fit(disp=-1)
        except:
            continue

        aic = model.aic
        results.append([param, aic])
    result_df = pd.DataFrame(results)
    result_df.columns = ['(p,q)x(P,Q)', 'AIC']
    # Sort in ascending order, lower AIC is better
    result_df = result_df.sort_values(by='AIC', ascending=True).reset_index(drop=True)

    return result_df


def timedelta(date, df_station):
    # function to determine period between two dates in terms of months
    y = ((date.year - df_station.index[len(df_station) - 1].year) * 12)
    if date.month > df_station.index[len(df_station) - 1].year:
        m = date.month - df_station.index[len(df_station) - 1].year
    else:
        m = date.month
    return y + m


# forecasting function
def forecasting(date, station):
    if len(date) == 2:
        # from_date = datetime.datetime.strptime(date[0], '%Y-%m-%d')
        start = timedelta(date[0], df_station)
        # to_date = datetime.datetime.strptime(date[1], '%Y-%m-%d')
        end = timedelta(date[1], df_station)
    elif len(date) == 1:
        # from_date = datetime.datetime.strptime(date[0]
        start = timedelta(date[0], df_station)
        st.write(start)

    p = range(0, 4, 1)
    d = 1
    q = range(0, 4, 1)
    P = range(0, 4, 1)
    D = 1
    Q = range(0, 4, 1)
    s = 4

    parameters = product(p, q, P, Q)
    parameters_list = list(parameters)

    result_df = sarimax(parameters_list, 1, 1, 4, df_station)

    p = result_df['(p,q)x(P,Q)'][0][0]
    q = result_df['(p,q)x(P,Q)'][0][1]
    P = result_df['(p,q)x(P,Q)'][0][2]
    Q = result_df['(p,q)x(P,Q)'][0][3]
    best_model = SARIMAX(df_station, order=(p, d, q), seasonal_order=(P, D, Q, s)).fit(dis=-1)
    # forecasting

    if len(date) == 2:
        forecast = best_model.predict(start=start, end=end)
    elif len(date) == 1:
        st.write(start)
        forecast = best_model.predict(start=start)

    return list(forecast)

# # plotting
# def plot(forecast):
#     forecast1 = df_station.append(forecast)
#     plt.figure(figsize=(15, 7.5))
#     plt.plot(forecast1, color='r', label='model')
#     plt.axvspan(df_station.index[-1], forecast.index[-1], alpha=0.5, color='lightgrey')
#     plt.plot(df_station, label='actual')
#     plt.legend()

# reading our preprocessed entry_exit data
grouped_df = pd.read_csv("Graph_Data/station_counts_grouped_per_station.csv")
station_codes = pd.read_csv("Graph_Data/station_nlc_codes.csv")

# creating a dictionary for station to NLC codes key value pairs
stations_dict = dict(zip(station_codes.Station, station_codes.NLC))

try:
    stations = st.multiselect(
        "Choose Station to view Plot", list(stations_dict.keys()), ["Green Park"]
    )
    # plotting for green park station alone
    # per station grouping of our data - green park station for a start

    if not stations:
        st.error("Please select at least one Station to view Plots.")
    else:
        count = 1
        for station in stations:
        # for station in stations:
            col1, col2 = st.columns([3, 1], gap="small")
            with col1:
                st.markdown(
                    f"""
                         ### {station} Station
                    """
                )
                green_park_data = grouped_df[grouped_df['NLC'] == stations_dict.get(station)].reset_index()[
                    ['Month-Year', 'Count of Taps']]
                # progress_bar = st.sidebar.progress(0)
                # status_text = st.sidebar.empty()
                # df = green_park_data.to_numpy()
                data = green_park_data.set_index('Month-Year')
                last_rows = data[:1]
                chart = st.line_chart(last_rows, use_container_width=True
                                      )
                for i in range(green_park_data.shape[0]):
                    new_rows = data[:i + 1]
                    # status_text.text("%i%% Complete" % i)
                    chart.add_rows(new_rows)
                    # progress_bar.progress(i)
                    last_rows = new_rows
                    time.sleep(0.05)
            with col2:
                station = int(station_codes['NLC'][station_codes['Station'] == station].unique())
                df_station = df['Count of Taps'][df['NLC'] == station].copy()

                date = []
                st.write("Choose Date:")
                # col3, col4 = st.columns(2, gap = "small")
                # with col3:
                d = st.date_input("At", key=count)
                # with col4:
                # e = st.date_input("To", key = count+1)
                count += 1
                if st.button("Predict", key=count):
                    y = str(d.year)
                    m = str(d.month)
                    m_n = d.strftime("%B")
                    y_m = y + '-' + m + '-' + '01'
                    da = datetime.strptime(y_m, '%Y-%m-%d')
                    date.append(d)

                    forecast = forecasting(date, station)
                    st.write('Forecast Population for ', m_n, 'in ', y, ': ', forecast)
                    # plot(forecast)


except URLError as e:
    st.error(
        """
        **This Dashboard requires internet access.**
        Connection error: %s
    """
        % e.reason
    )

# rerun.
st.button("Re-run")