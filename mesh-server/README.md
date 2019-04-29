# How to setup for demo
* Start MQTT server on Mac. (My mac auto starts by default) or run "mosquitto" to start default on 1883 port
* Start node server by "node app.js"
* Go to nrf\_reader folder, for test without real boards, run "python mqtt\_py\_server.py"
* For demo and testing with real boards, run "python reader.py"
* mosquitto\_sub -t topic

