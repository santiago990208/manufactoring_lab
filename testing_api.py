import json
import time
import requests
import base64
import datetime
from rich import print
url_api = "https://iotdemo00182.cna.phx.demoservices005.iot.oraclepdemos.com/productionMonitoring/clientapi/v2/workOrders"
query = '?q={"name": { "$like":"WO-410-1081" } }'
url = url_api+query

username = "iotadmin.00182"
password = "4SG#leB4rOd3"

org_id_old = "6BNYV2GM1F1G"
org_id_SUPREMO = "6KQBWCBW1F1G"


auth_string = f"{username}:{password}"
auth_bytes = auth_string.encode("utf-8")
b64_auth_string = base64.b64encode(auth_bytes).decode("utf-8")

headers = {
    "Authorization": f"Basic {b64_auth_string}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-ORACLE-IOT-ORG": org_id_SUPREMO,
}

def testing_workorder(headers,url):
    headers.update({"X-HTTP-Method-Override": "PATCH"})
    response = requests.get(url, headers=headers, verify=False)
    workorder = ""
    print(response.json())
    if response.status_code == 200:
        data = response.json()
        if(data['items']):
            workorder = data['items'][0]
            now = datetime.datetime.now()
            print(workorder['systemState'])
            planned_start_time = datetime.datetime.fromtimestamp(round(workorder["plannedStartTime"] / 1000)) # format to compare wiuth now time
            # b = datetime.datetime.fromtimestamp(round(workorder["plannedEndTime"] / 1000))
            planned_quantity = workorder["plannedQuantity"]
            # d = workorder["systemState"]
            workorderId = workorder['id']
            print(now)
            print(planned_start_time)
            if now > planned_start_time:
                print(f'send order of: {planned_quantity:.0f} blocks')
            
                data = {
                    "actualEndTime": int(time.time()),
                    "state": "COMPLETE", #COMPLETED
                    "systemState": "COMPLETE", #COMPLETED
                }
            
            json_data = json.dumps(data)
            print(json_data)

            requests.post(url+"/WO-410-1081", headers=headers, data=json_data, verify=False)

    else:
        print("Request failed with status code: {}".format(response.status_code))
    headers.popitem()

def testing_iot_devices(headers):
    url_link_airpicker = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/airpickerConnector"
    url_link_laser = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/laserConnector"
    url_link_qualitycontrol = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/qualityConnector"
    data_air= {
        "id": "airpickerState",
        "state": "IDLE",
        "accelerometer": 1.8
    }
    json_data_air = json.dumps(data_air)
    a = requests.post(url_link_airpicker, headers=headers, data=json_data_air, verify=False)
    print(a)
    data_laser = {
        "id": "laserState",
        "state": "IDLE",
        "accelerometer": 1.0
    }
    json_data_laser = json.dumps(data_laser)
    a = requests.post(url_link_laser, headers=headers, data=json_data_laser, verify=False)
    print(a)
    data_quality = {
        "id": "qualityControl",
        "state": "IDLE",
        "gravingCheck": "Approved"
    }
    json_data_quality = json.dumps(data_quality)
    a = requests.post(url_link_qualitycontrol, headers=headers, data=json_data_quality, verify=False)
    print(a)

testing_workorder(headers,url)
# i = 0
# while i < 10:
#     testing_iot_devices(headers)
#     i = i +1



