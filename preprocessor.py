import re
import pandas as pd

# Android 24h:  "DD/MM/YYYY, HH:MM - "
ANDROID_PATTERN = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s'
# Android 12h:  "M/D/YY, H:MM AM/PM - "
ANDROID_12H_PATTERN = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[AP]M\s-\s'
# iOS:          "[DD/MM/YY, H:MM:SS AM/PM] "
IOS_PATTERN = r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\s[AP]M\]\s'

def preprocessor(data):
    # Detect format
    if re.search(IOS_PATTERN, data):
        pattern = IOS_PATTERN
        fmt = 'ios'
    elif re.search(ANDROID_12H_PATTERN, data):
        pattern = ANDROID_12H_PATTERN
        fmt = 'android_12h'
    else:
        pattern = ANDROID_PATTERN
        fmt = 'android_24h'

    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})

    if fmt == 'ios':
        # "[23/11/25, 8:57:15 AM] " -> "23/11/25, 8:57:15 AM"
        df['message_date'] = df['message_date'].str.strip().str.strip('[]')
        df['message_date'] = pd.to_datetime(df['message_date'], format='%d/%m/%y, %I:%M:%S %p')
    elif fmt == 'android_12h':
        # "5/9/23, 9:32 PM - " -> "5/9/23, 9:32 PM"
        df['message_date'] = df['message_date'].str.strip().str.rstrip(' -').str.strip()
        df['message_date'] = pd.to_datetime(df['message_date'], format='%m/%d/%y, %I:%M %p')
    else:
        df['message_date'] = pd.to_datetime(df['message_date'], format='%d/%m/%Y, %H:%M - ')

    df.rename(columns={'message_date': 'date'}, inplace=True)

    #separate user and message
    users = []
    messages = []
    for message in df['user_message']:
        entry = re.split(r'([\w\W]+?):\s', message)
        if entry[1:]:  # user name exists
            users.append(entry[1])
            messages.append(entry[2])
        else:
            users.append('group_notification')
            messages.append(entry[0])

    df['user'] = users
    df['message'] = messages
    df.drop(columns=['user_message'], inplace=True)

    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    period = []
    for hour in df[['day_name', 'hour']]['hour']:
        if hour == 23:
            period.append(str(hour) + "-" + str('00'))
        elif hour == 0:
            period.append(str('00') + "-" + str(hour+1))
        else:
            period.append(str(hour) + "-" + str(hour+1))

    df['period'] = period
    return df
