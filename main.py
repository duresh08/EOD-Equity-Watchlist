from nsedt import equity as eq
import pandas as pd
import datetime as dt
from datetime import datetime, timedelta
from nselib import capital_market
import pandas_ta as ta
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
import smtplib
import sys
import streamlit as st

def Email_sender(Output_msg, tickdate):
    password_mail = st.secrets["password"]
    if Output_msg.empty == False:
        msg = MIMEMultipart()
        msg['Subject'] = "EOD Equity Watchlist: {}".format(tickdate)
        msg['From'] = 'dhruv.suresh2@gmail.com'
        html = """\
        <html>
          <head></head>
          <body>
            {0}
          </body>
        </html>
        """.format(Output_msg.to_html())
        part1 = MIMEText(html, 'html')
        msg.attach(part1)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('dhruv.suresh2@gmail.com', password_mail)
        server.sendmail(msg['From'], 'dhruv.suresh2@gmail.com' , msg.as_string())
        server.close()
    else:
        print("no mail to send for date {}".format(tickdate))
        pass

def main_function(df):
    Stoch = round(ta.stoch(high = df["high"], low = df["low"], close = df["close"], window = 14, smooth_window = 3),2)
    df["%K"] = Stoch["STOCHk_14_3_3"]
    df["%D"] = Stoch["STOCHd_14_3_3"]
    if symbol[-3:] == "JPY":
        rounding = 3
    else:
        rounding = 5
    Heiken_Ashi = round(ta.ha(df["open"], high = df["high"], low = df["low"], close = df["close"]), rounding)
    Bollinger_bands = round(ta.bbands(close = df["close"], length = 20, std = 2), rounding)
    df['BBL'] = Bollinger_bands['BBL_20_2.0']
    df['BBU'] = Bollinger_bands['BBU_20_2.0']
    df["HA open"] = Heiken_Ashi["HA_open"]
    df["HA high"] = Heiken_Ashi["HA_high"]
    df["HA low"] = Heiken_Ashi["HA_low"]
    df["HA close"] = Heiken_Ashi["HA_close"]
    df["200 EMA"] = round(ta.ema(df["close"], 200), rounding)
    df["9 EMA"] = round(ta.ema(df["close"], 9), rounding)
    df["ATR"] = round(ta.atr(df["high"], df["low"], df["close"], 14), rounding)
    df = df[pd.isna(df['200 EMA']) == False].reset_index(drop = True)
    df.loc[(df['HA close'] - df['HA open']) >= 0, 'HA_bool'] = 1
    df.loc[(df['HA close'] - df['HA open']) < 0, 'HA_bool'] = 0
    df.loc[(df['HA_bool'] != df['HA_bool'].shift(1)), 'HA_flip_bool'] = (df['HA_bool'] - df['HA_bool'].shift(1))
    non_na_flip_idx = df.loc[~pd.isna(df['HA_flip_bool'])].index
    for i,j in  zip(non_na_flip_idx, non_na_flip_idx[1:]):
        temp_df = df.iloc[i : j + 1]
        if temp_df.iloc[-1]['HA_flip_bool'] == -1:
            df.at[j, '%K_high'] = temp_df['%K'].max()
            df.at[j, '%D_high'] = temp_df['%D'].max()
            df.at[j, 'close_high'] = temp_df['close'].max()
            df.at[j, '%K_low'] = temp_df['%K'].min()
            df.at[j, '%D_low'] = temp_df['%D'].min()
            df.at[j, 'close_low'] = temp_df['close'].min()
        if temp_df.iloc[-1]['HA_flip_bool'] == 1:
            df.at[j, '%K_low'] = temp_df['%K'].min()
            df.at[j, '%D_low'] = temp_df['%D'].min()
            df.at[j, 'close_low'] = temp_df['close'].min()
            df.at[j, '%K_high'] = temp_df['%K'].max()
            df.at[j, '%D_high'] = temp_df['%D'].max()
            df.at[j, 'close_high'] = temp_df['close'].max()
    df.loc[~pd.isna(df['close_high']), 'close_high_shift'] = df.loc[~pd.isna(df['close_high']), 'close_high'].shift(1)
    df.loc[~pd.isna(df['close_low']), 'close_low_shift'] = df.loc[~pd.isna(df['close_low']), 'close_low'].shift(1)
    df.loc[~pd.isna(df['%K_high']), '%K_high_shift'] = df.loc[~pd.isna(df['%K_high']), '%K_high'].shift(1)
    df.loc[~pd.isna(df['%K_low']), '%K_low_shift'] = df.loc[~pd.isna(df['%K_low']), '%K_low'].shift(1)
    df.loc[~pd.isna(df['%D_high']), '%D_high_shift'] = df.loc[~pd.isna(df['%D_high']), '%D_high'].shift(1)
    df.loc[~pd.isna(df['%D_low']), '%D_low_shift'] = df.loc[~pd.isna(df['%D_low']), '%D_low'].shift(1)
    df['%K_low'] = df['%K_low'].ffill()
    df['%D_low'] = df['%D_low'].ffill()
    df['%K_high'] = df['%K_high'].ffill()
    df['%D_high'] = df['%D_high'].ffill()
    df['close_low'] = df['close_low'].ffill()
    df['close_high'] = df['close_high'].ffill()
    df['HA_flip_bool'] = df['HA_flip_bool'].ffill()
    df['%K_low_shift'] = df['%K_low_shift'].ffill()
    df['%D_low_shift'] = df['%D_low_shift'].ffill()
    df['%K_high_shift'] = df['%K_high_shift'].ffill()
    df['%D_high_shift'] = df['%D_high_shift'].ffill()
    df['close_low_shift'] = df['close_low_shift'].ffill()
    df['close_high_shift'] = df['close_high_shift'].ffill()
    df.loc[df['HA_flip_bool'] != df['HA_flip_bool'].shift(1), 'counter_bool'] = 1
    counter = 0
    for i in range(df.shape[0]):
        if df.iloc[i]['counter_bool'] == 1:
            counter = 1
            df.at[i, 'counter'] = counter
        else:
            if counter != 0:
                counter += 1
                df.at[i, 'counter'] = counter
            else:
                continue
    df['counter_prev'] = df['counter'].shift(1)
    df.loc[(df['counter_bool'] == 1), 'counter_prev'] = df.loc[(df['counter_bool'] == 1), 'counter_prev']
    df.loc[(df['counter_bool'] != 1), 'counter_prev'] = math.nan
    df['counter_prev'] = df['counter_prev'].ffill()
    df['candle_counter'] = df['counter_prev'] + df['counter']
    df.loc[(df['HA_flip_bool'] == 1) & (df['close'] > df['close_high_shift']) & (df['%K'] < df['%K_high_shift'])
      & (df['%K_low_shift'] < 50) & (df['close'] > df['BBU']) & (df['%K_low'] < 50) & (df['%D'] < df['%D_high_shift'])
           & (df['%K_high_shift'] > 80) & (df['%D_high_shift'] > 80) & (df['candle_counter'] >= 10)
           & (df['close'] > df['open']), 'divergence'] = 'short'
    df.loc[(df['HA_flip_bool'] == -1) & (df['close'] < df['close_low_shift']) & (df['%K'] > df['%K_low_shift'])
          & (df['%K_high_shift'] > 50) & (df['close'] < df['BBL']) & (df['%K_high'] > 50) & (df['%D'] > df['%D_low_shift'])
           & (df['%K_low_shift'] < 20) & (df['%D_low_shift'] < 20) & (df['candle_counter'] >= 10)
           & (df['close'] < df['open']), 'divergence'] = 'long'
    return df

def get_data(symbol, start_date, end_date):
    df = capital_market.price_volume_and_deliverable_position_data(symbol = symbol, from_date = start_date, to_date = end_date)
    df = df.loc[:,['Symbol','Date','OpenPrice','HighPrice','LowPrice','ClosePrice']]
    df.columns = ['symbols','tickdate','open','high','low','close']
    df['symbols'] = symbol
    df = df.dropna(axis = 0)
    df['open'] = df['open'].apply(lambda x: float("".join(str(x).split(","))))
    df['high'] = df['high'].apply(lambda x: float("".join(str(x).split(","))))
    df['low'] = df['low'].apply(lambda x: float("".join(str(x).split(","))))
    df['close'] = df['close'].apply(lambda x: float("".join(str(x).split(","))))
    return df


end_date = dt.datetime.now().strftime("%d-%m-%Y")
start_date = (dt.datetime.now() - dt.timedelta(days = 500)).strftime("%d-%m-%Y")
output_df = pd.DataFrame()
symbols_list = sorted(eq.get_symbols_list())

while True:
    if dt.datetime.now().weekday() in range(5):
        if dt.datetime.now().strftime("%H:%M:%S") == "22:00:00":
            for s in symbols_list:
                try:
                    print("running for symbol: {}, date: {}".format(s, end_date))
                    df = get_data(s, start_date, end_date)
                    df = main_function(df)
                    if df.iloc[-2]['divergence'] == "long":
                        if ((df.iloc[-1]['close'] > df.iloc[-1]['open']) & (df.iloc[-1]['close'] > df.iloc[-1]['200 EMA']) &
                           (df.iloc[-1]['%K'] > df.iloc[-2]['%K_low_shift']) & (df.iloc[-1]['%D'] > df.iloc[-2]['%D_low_shift']) &
                            (df.iloc[-1]['close'] < df.iloc[-1]['9 EMA'])):
                            output_df_dict = {"symbol": symbol, "tickdate": end_date}
                            output_df = pd.concat([output_df, pd.DataFrame.from_dict(output_df_dict).T]).reset_index(drop = True)
                    elif df.iloc[-2]['divergence'] == "short":
                        if ((df.iloc[-1]['close'] < df.iloc[-1]['open']) & (df.iloc[-1]['close'] < df.iloc[-1]['200 EMA']) &
                           (df.iloc[-1]['%K'] < df.iloc[-2]['%K_high_shift']) & (df.iloc[-1]['%D'] < df.iloc[-2]['%D_high_shift']) &
                            (df.iloc[-1]['close'] > df.iloc[-1]['9 EMA'])):
                            output_df_dict = {"symbol": symbol, "tickdate": end_date}
                            output_df = pd.concat([output_df, pd.DataFrame.from_dict(output_df_dict).T]).reset_index(drop = True)
                    else:
                        continue
                except:
                    print("error for symbol: {}, date: {}".format(s, end_date))
                    continue
            Email_sender(output_df, end_date)
        else:
            time.sleep(60)
            continue
    else:
        time.sleep(60)
        continue
