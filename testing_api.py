##ESTE ARHIVO ES NETAMENTE DE TESTING
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
password = "pyNX#qQxh89k"

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
    print(headers)
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

i = 0
while i < 10:
    #  testing_iot_devices(headers)
     i = i +1



def testing_iot_cs(headers):
    url_connector_state = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/test_machineState"
    data_state= {
        "id": "test_machineState",
        "state": "IDLE",
    }
    json_data_state = json.dumps(data_state)
    print(json_data_state)
    state_report = requests.post(url_connector_state, headers=headers, data=json_data_state, verify=False)
    print(state_report)

    url_connector_state_airpicker = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/airpicker_connector"
    data_state_airpicker= {
        "id": "test_machineState",
        "state": "DOWN",
        "accelerometer": 1,
    }
    json_data_state_airpicker = json.dumps(data_state_airpicker)
    print(json_data_state_airpicker)
    state_report_airpicker = requests.post(url_connector_state_airpicker, headers=headers, data=json_data_state_airpicker, verify=False)
    print(state_report_airpicker)
    
    url_connector_ouput = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/test_productionOutput"
    data_ouput= {
        "modelID": "outPutModel",
        "startTime": int(time.time()), #Date & Time
        "endTime": int(time.time()), #Date & Time
        "product": "7G2C9VKC18S0", #String
        "quantity": "9", #Number
        "badQuantity": "1", #Number
        "factory": "300000178327892", #String
        "machine": "SCM_300000203675710", #String
        "workOrderNumber": "300000260047145", #String
        "operationNumber": "10", #Integer
        "resourceNumber": "1", #Integer
        "productionLine": "", #String
        "routingTask": "7G2C9W4W18S0", #String
    }
    json_data_ouput = json.dumps(data_ouput)
    print(json_data_ouput)
    ouput_report = requests.post(url_connector_ouput, headers=headers, data=json_data_ouput, verify=False)
    print(ouput_report)

i = 0
while i < 10:
     testing_iot_cs(headers)
     i = i +1
