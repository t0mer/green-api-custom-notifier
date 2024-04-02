# green-api-custom-notifier

[green-api](https://green-api.com/en) is a service that allows us to send and receive text, photo and video using stable WhatsApp API gateway. The service includes free account that can be used to send notifications to 3 chats (Group or Private) and many more.


[green-api-custom-notifier](https://github.com/t0mer/green-api-custom-notifier) is a [Homeassistant ](https://www.home-assistant.io/) custom notification component that enables us to send notification to Whatsapp groups using [green-api](https://green-api.com/en).


## Limitations
* The free account is limited to 3 chats (Group or Private).


## Getting started

### Setup Green API account
Nevigate to [https://green-api.com/en](https://green-api.com/en) and register for a new account:
![Register](screenshots/register.png)

Fill up your details and click on **Register**:
![Create Account](screenshots/create_acoount.png)


Next, click on the "Create an instance":
![Create Instance](screenshots/create_instance.png)


Select the "Developer" instance (Free):
![Developer Instance](screenshots/developer_instance.png)


Copy the InstanceId and Token, we need it for the integration settings:
![Instance Details](screenshots/instance_details.png)

Next, Lets connect our whatsapp with green-api. On the left side, Under API --> Account, click on QR and copy the QR URL to the browser and click on "Scan QR code"

![Send QR](screenshots/send_qr.png)

![Scan QR](screenshots/scan_qr.png)

Next, Scan the QR code to link you whatsapp with Green API:

![QR Code](screenshots/qr.png)




```yaml
notify:
  - platform: greenapi
    name: greenapi
    instance_id:  #Set the instanceid
    token:  #Set the greenapi token.
    target: #Comma separated values. Contact should end with @c.us and group with @g.us
```
