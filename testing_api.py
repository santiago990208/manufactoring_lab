import json
import requests
import base64
import datetime
from rich import print
url_api = "http://iotdemo00182.cna.phx.demoservices005.iot.oraclepdemos.com/productionMonitoring/clientapi/v2/workOrders"
query = '?q={"systemState": { "$like":"RELEASED" } }'
url = url_api+query

username = "iotadmin.00182"
password = "YTmIj#4g0kmG"

org_id = "6BNYV2GM1F1G"

auth_string = f"{username}:{password}"
auth_bytes = auth_string.encode("utf-8")
b64_auth_string = base64.b64encode(auth_bytes).decode("utf-8")

headers = {
    "Authorization": f"Basic {b64_auth_string}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-ORACLE-IOT-ORG": "6BNYV2GM1F1G"
}


response = requests.get(url, headers=headers, verify=False)

if response.status_code == 200:
    data = response.json()
    workorder = data['items'][0]
    now = datetime.datetime.utcnow()
    
    planned_start_time = datetime.datetime.fromtimestamp(round(workorder["plannedStartTime"] / 1000)) # format to compare wiuth now time
    # b = datetime.datetime.fromtimestamp(round(workorder["plannedEndTime"] / 1000))
    planned_quantity = workorder["plannedQuantity"]
    # d = workorder["systemState"]
    if now > planned_start_time:
        print(f'send order of: {planned_quantity:.0f} blocks')

else:
    print("Request failed with status code: {}".format(response.status_code))


print(workorder)
# AirpickerProductionMonitoringMachineState
# Airpicker Production Monitoring Machine State device model
#urn:com:supremomanufactoring:airpickerdevice:airpickerblock

url_link_airpicker = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/airpickerConnector"
url_link_laser = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/laserConnector"
url_link_qualitycontrol = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/productionlineConnector"
url_production_line = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/productionlineController"
data= {
    "id": "qualityControl",
    "factory": "300000178327892", 
    "state": "IDLE",
    "product": "6C8T01CM1CYG", 
    "quantity": 10.0,#total dinamic
    "gravingCheck": "approved",
    "blockApproved": 9, #dinamic counter
    "blockRejected": 1,#dinamic counter
    "startTime": 1674755220000,#unix
    "endTime": 1674762420000 #unix
}

json_data = json.dumps(data)
print(json_data)
print(requests.post(url_production_line, headers=headers, data=json_data, verify=False))