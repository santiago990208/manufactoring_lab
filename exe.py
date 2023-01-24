from lab_manufactura import manufacturing_laboratory

username = "iotadmin.00182"
password = "IN#O9KiqQXMM"
to_produce = 2
port_arm_airpicker= "/dev/ttyACM1"
port_arm_laser = "/dev/ttyACM0",
url_link_qualitycontrol = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/Quality_Control_Connector"
url_link_airpicker = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/Airpicker_Connector"
url_link_laser = "https://iotdemo00182.device.cna.phx.demoservices005.iot.oraclepdemos.com/cgw/Laser_Connector"
url_link_vibration = ""
url_link_aproved = ""
url_link_rejected = ""

manufactory = manufacturing_laboratory(username = username, password = password, to_produce = to_produce, port_arm1= port_arm_airpicker , port_arm2 = port_arm_laser, url_airpicker =url_link_airpicker,url_laser =url_link_laser,url_belt = url_link_qualitycontrol, url_vibration =url_link_vibration, url_counter_aproved = url_link_aproved, url_counter_rejected = url_link_rejected)

print(manufactory.start_process())