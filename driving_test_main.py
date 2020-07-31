import requests
from pprint import pprint
import os
import platform
import re
import time
from datetime import date, timedelta

bearer_token = ''

current_os = platform.system()

# date in yyyy-mm-dd format
start_date = date(2020, 12, 1)
end_date = date(2021, 1, 15)

city_coordinates = '53.34806823730469,-6.248270034790039'  # Dublin coordinates
# distance range in miles
distance_range = 200


def get_token():
    o = requests.get("https://eu-proscheduler.prometric.com").text
    arguments = re.findall(r"bootstrapApp(.+)", o)[0]
    global bearer_token
    bearer_token = eval(arguments.split(',')[13])


def create_headers():
    return {
        "accept": "application/json, text/plain, */*", "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "authorization": f"Bearer {bearer_token}",
        "content-type": "application/json", "sec-fetch-mode": "cors", "sec-fetch-site": "same-site",
        "x-http-method-override": "SEARCH"}


def create_url(start_date, end_date):
    return f"https://eu-scheduling.prometric.com/api/v1/sites/availabilities/?startDate={start_date}T00%3A00%3A00&endDate={end_date}T00%3A00%3A00&coordinates={city_coordinates}&Take=5&skip=0"


def send_request(url, headers):
    return requests.post(url, headers=headers,
                             data="[{\"id\":\"_UzoSDjoA0i3Smyv2e_bpg\",\"testingAccommodations\":[]}]")


def get_appointments(url):
    headers = create_headers()
    response = send_request(url, headers)

    if response.status_code != 200:
        get_token()
        headers = create_headers()
        response = send_request(url, headers)
        sound_alert(2)

    return response


def sound_alert(n):
    duration = n
    freq = 440  # Hz
    if current_os == 'Linux':
        #you need sox package to run this
        #use this command to install sudo apt-get install sox
        os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))
    elif current_os == 'Windows':
        import winsound
        winsound.Beep(freq, duration * 1000)
    elif current_os == 'Darwin':
        os.system('say "Found an appointment"')
    else:
        raise Exception('OS not supported')

#get token and user from pushover.net
def notify(message):
    requests.post("https://api.pushover.net/1/messages.json", data={
        "token": "",
        "user": "",
        "message": message
    })


if start_date > end_date:
    raise Exception("End date should be after start date")

get_token()

while True:
    startDate = start_date
    endDate = ''
    while startDate < end_date:
        if (startDate + timedelta(days=14)) < end_date:
            endDate = startDate + timedelta(days=14)
        else:
            endDate = end_date

        url = create_url(startDate, endDate)
        print(url)

        r = get_appointments(url)
        results = r.json()['results']

        num_appointments = 0

        valid_results = {}

        for result in results:
            if result['location']['distance'] < distance_range:
                num_appointments += 1
                locality = result['location']['address']['locality']
                availability = result['availability']
                valid_results[locality] = availability

        if num_appointments > 0:
            sound_alert(5)
            print(
                'Found {} appointment(s) between {} and {} within {} miles'.format(num_appointments, startDate, endDate,
                                                                                   distance_range))
            print(valid_results)
            #pprint(r.json())   # print entire json response#

            #Uncomment following two lines after getting keys from pushover.net
            # notify(
            #    f"Found {num_appointments} appointment(s) between {startDate} and {endDate} within {distance_range} miles")

        startDate = endDate + timedelta(days=1)
    print()
    time.sleep(30)
