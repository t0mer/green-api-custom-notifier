# green-api-custom-notifier

[Green-API](https://green-api.com/en) is a service that lets you send and receive text, photos and videos through a stable WhatsApp API gateway. It includes a free account that can send notifications to 3 chats (group or private), among other features.

[green-api-custom-notifier](https://github.com/t0mer/green-api-custom-notifier) is a [Home Assistant](https://www.home-assistant.io/) custom notification component (installable through HACS) that sends notifications to WhatsApp contacts and groups using [Green-API](https://green-api.com/en).

## Table of contents

- [Features](#features)
- [Requirements](#requirements)
- [Limitations](#limitations)
- [Getting started](#getting-started)
  - [Set up a Green-API account](#set-up-a-green-api-account)
  - [Get the contacts and groups](#get-the-contacts-and-groups)
  - [Install the component](#install-the-component)
  - [Set up the notification in Home Assistant](#set-up-the-notification-in-home-assistant)
- [Configuration reference](#configuration-reference)
- [Sending a message](#sending-a-message)
  - [Optional: attach media to the message](#optional-attach-media-to-the-message)
  - [Automation example](#automation-example)
- [Troubleshooting](#troubleshooting)
- [Known issues](#known-issues)
- [Security notes](#security-notes)
- [Contributing](#contributing)
- [License](#license)

## Features

- `notify` platform named `greenapi`, configured in `configuration.yaml`; each entry creates a `notify.<name>` action.
- Sends text messages to a WhatsApp contact (`...@c.us`) or group (`...@g.us`).
- Optional default target in the configuration, which a `target` in the action call overrides.
- Optional `title`, sent in **bold** on the first line of the message.
- Sends a local file (image, document, and so on) with the message as its caption: the file is uploaded to Green-API and then sent to the chat.
- Link previews are turned off for text messages.

## Requirements

- A running Home Assistant instance with access to the `config` folder (for `custom_components` and `configuration.yaml`).
- A [Green-API](https://green-api.com/en) account and an instance linked to a WhatsApp account (see below).
- Outbound internet access from Home Assistant to Green-API.
- The Python library [`whatsapp-api-client-python`](https://pypi.org/project/whatsapp-api-client-python/), which Home Assistant installs automatically from the component's `manifest.json`.

## Limitations

- The free account is limited to 3 chats (group or private). <!-- TODO: verify current Green-API free-plan limits -->
- A message is sent to one chat only. If you pass a list of targets, only the first one is used.
- Media can only be sent from a file path that Home Assistant can read; URLs are not supported.

## Getting started

### Set up a Green-API account

Navigate to [https://green-api.com/en](https://green-api.com/en) and register for a new account:
![Register](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/register.png)

Fill in your details and click **Register**:
![Create Account](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/create_acoount.png)

Next, click **Create an instance**:
![Create Instance](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/create_instance.png)

Select the **Developer** instance (free):
![Developer Instance](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/developer_instance.png)

Copy the instance ID and token; you need them for the integration settings:
![Instance Details](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/instance_details.png)

Next, connect your WhatsApp account to Green-API. On the left side, under **API** → **Account**, click **QR**, copy the QR URL into the browser and click **Scan QR code**:

![Send QR](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/send_qr.png)

![Scan QR](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/scan_qr.png)

Scan the QR code with WhatsApp to link your account with Green-API:

![QR Code](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/qr.png)

Once the account is linked, the green light in the instance header shows that the instance is active:
![Active Instance](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/active_instance.png)

### Get the contacts and groups

Before you can start messaging, you need the contact or group ID. You can get it from a Green-API endpoint.
On the left side, under **API** → **Service methods**, click **getContacts** and then click **Send**:
![Get Contacts](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/get_contacts.png)

The result is the list of contacts and groups:
- A contact ID ends with **@c.us**.
- A group ID ends with **@g.us**.

![Contacts Lists](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/contacts_list.png)

Write down the ID; you need it to configure the notification. The component sends the ID to Green-API exactly as written and does not add the `@c.us` / `@g.us` suffix for you, so always use the full ID.

### Install the component

**HACS (custom repository)**

1. In HACS, open the menu (⋮) → **Custom repositories**.
2. Add `https://github.com/t0mer/green-api-custom-notifier` with the category **Integration**.
3. Search for **Green API whatsapp custom notification / notify** in HACS and download it.
4. Restart Home Assistant.

**Manual**

1. Download [green-api-custom-notifier](https://github.com/t0mer/green-api-custom-notifier).
2. Copy the `custom_components/greenapi` folder into your Home Assistant `config/custom_components` folder, so that you have `config/custom_components/greenapi/notify.py`.
3. Restart Home Assistant.

### Set up the notification in Home Assistant

This is a YAML-configured `notify` platform; there is no UI config flow. Add the following section to your `configuration.yaml` file and restart Home Assistant:

```yaml
notify:
  - platform: greenapi
    name: greenapi
    instance_id: !secret greenapi_instance_id  # REQUIRED: the Green-API instance ID
    token: !secret greenapi_token              # REQUIRED: the Green-API instance token
    target: 972*********@c.us                  # OPTIONAL: the default target. If you set it here, you don't have to specify it again in your action calls.
```

And in `secrets.yaml`:

```yaml
greenapi_instance_id: "1101000000"
greenapi_token: "your-green-api-token"
```

- `instance_id` is the Green-API instance ID.
- `token` is the Green-API instance token.
- `target` is the chat, contact or group ID to send the message to:
  - For groups, the ID must end with `@g.us`.
  - For chats, the ID must end with `@c.us`.

The `name` sets the action name: `name: greenapi` creates `notify.greenapi`. You can add several entries with different names (for example, one per group).

## Configuration reference

| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `platform` | Yes | – | Must be `greenapi`. |
| `name` | No | `notify` | Name of the notify action (`notify.<name>`). Standard Home Assistant notify option. |
| `instance_id` | Yes | – | Green-API instance ID. |
| `token` | Yes | – | Green-API instance token. |
| `target` | No | – | Default chat ID (`...@c.us` for a contact, `...@g.us` for a group). Overridden by `target` in the action call. |
| `title` | No | – | Accepted by the schema but not used by the component; set `title` in the action call instead. |

## Sending a message

To send a message, call the action and provide the following parameters:

- `message` (**required**): the text to send.
- `title` (**optional**): a title for the message, sent in **bold** on the first line.
- `target` (**optional** if you've defined a default target in the notify configuration, otherwise required): the chat or group ID to send the message to. If you pass a list, only the first ID is used.

![Send text message](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/text_message.png)

Or in YAML mode:

```yaml
action: notify.greenapi
data:
  message: New WhatsApp component
  title: Home Assistant
  target: 972*********@c.us
```

On Home Assistant versions older than 2024.8, use `service:` instead of `action:`.

### Optional: attach media to the message

To send a message with media, add the following to the `data` parameter:

- `file`: the path to the file, as seen by Home Assistant (for example `/config/images/Capture.png`).

The file is uploaded to Green-API and sent to the chat, with the message (including the title, if any) as its caption.

![Send media](https://raw.githubusercontent.com/t0mer/green-api-custom-notifier/main/screenshots/send_media.png)

Or in YAML mode:

```yaml
action: notify.greenapi
data:
  message: New WhatsApp component
  target: 972*********@c.us
  data:
    file: /config/images/Capture.png
```

#### Important

If the file path does not exist **and you pass `target` in the action call**, the message is still sent as plain text and a warning is logged. If you rely on the default `target` from the configuration, a missing file makes the action call fail and nothing is sent (see [Known issues](#known-issues)).

### Automation example

This example uses the `triggers:` / `trigger:` / `actions:` syntax, which needs Home Assistant 2024.10 or later. On older versions, use `trigger:` / `platform:` / `action:` with `service:`.

```yaml
automation:
  - alias: Notify WhatsApp group when the front door opens
    triggers:
      - trigger: state
        entity_id: binary_sensor.front_door
        to: "on"
    actions:
      - action: notify.greenapi
        data:
          title: Front door
          message: "The front door was opened at {{ now().strftime('%H:%M') }}"
          target: 120363000000000000@g.us
```

## Troubleshooting

- **No message arrives and nothing obvious happens.** The component does not check Green-API's responses to sending a message or file. Green-API HTTP errors are logged at ERROR level by the library itself, under the logger `whatsapp-api-client-python`, not by the component. Check **Settings** → **System** → **Logs** for entries from both `whatsapp-api-client-python` and `custom_components.greenapi.notify`. When you pass `target` in the action call, other send errors are caught and logged by the component. When you rely on the default `target`, they surface as a failed action call with a `TypeError` instead (see [Known issues](#known-issues)).
- **Messages don't reach the chat.** Make sure the target is a full ID ending with `@c.us` or `@g.us`; the component does not add the suffix. Also check that the Green-API instance is active (green light) and still linked to WhatsApp.
- **The file is not sent.** The path must exist inside the Home Assistant environment (for example under `/config`). With `target` passed in the action call, a missing file means only the text is sent and a warning is logged, and a failed upload to Green-API is logged as an error by the component. With the default `target`, both cases make the action call fail (see [Known issues](#known-issues)). If the upload succeeds but sending the file fails, the error appears only in the `whatsapp-api-client-python` log.
- **More logging.** To see the `Sending message to ...` log lines, enable info logging for the component:

  ```yaml
  logger:
    default: warning
    logs:
      custom_components.greenapi: info
      whatsapp-api-client-python: info
  ```

## Known issues

- **Default target and error handling.** When `target` is not passed in the action call (so the default `target` from the configuration is used), the warning and error log lines in `notify.py` fail with a `TypeError`. As a result, a missing file or any other send error makes the action call fail: nothing is sent and no warning or error from the component is logged. Until this is fixed, pass `target` explicitly in action calls that attach a file.
- **Unchecked API responses.** Responses from sending a message or a file are not checked by the component. Green-API errors appear only in the `whatsapp-api-client-python` log.

## Security notes

- The Green-API token gives full access to your linked WhatsApp account through Green-API. Keep it out of `configuration.yaml` by using `!secret` (as in the example above), and don't share `secrets.yaml`.
- Messages and files are sent through Green-API's cloud service, so they leave your network. Don't send anything you wouldn't trust to a third party.
- If a token leaks, regenerate it in the Green-API console and update `secrets.yaml`.

## Contributing

Issues and pull requests are welcome at [github.com/t0mer/green-api-custom-notifier](https://github.com/t0mer/green-api-custom-notifier/issues).

## License

This project is licensed under the [Apache License 2.0](LICENSE).
