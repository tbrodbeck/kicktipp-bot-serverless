# Serverless Kicktipp Bot

This script can automatically enter tips into [Kicktipp](https://www.kicktipp.com/) based on the quotes of the bookmakers. It is written in [Python](https://www.python.org/) and uses [Playwright](https://playwright.dev/) to interact with the website.

## Comparison to other tools

The main difference between this approach and [kicktipp-bot](https://github.com/antonengelhardt/kicktipp-bot) is that this tool is...
1. intended to be run as a job not as a service. So it will stop immediately after checking the games and requires an external scheduling tool such as Cron, [GCP Cloud Run Code Triggers](https://cloud.google.com/run/docs/triggering/trigger-with-events) or [AWS EventBridge](https://aws.amazon.com/eventbridge/).
2. using [Playwright](https://playwright.dev/) instead of [Selenium](https://www.selenium.dev/).

## Run

Copy the contents of the `.env.example` file into a new file called `.env` and fill in the values or deploy with Kubernetes.

Run `pip install -r requirements.txt` to install the dependencies.

## Environment Variables

| Variable | Description | Example | Required |
| --- | --- | --- | --- |
| `KICKTIPP_EMAIL` | Your Kicktipp email | `email@example.com` | Yes |
| `KICKTIPP_PASSWORD` | Your Kicktipp password | `password` | Yes |
| `KICKTIPP_NAME_OF_COMPETITION` | The name of the competition you want to tip for. This group is required because it will be used to look at the past games. Only if no other competition is used this one will be used with the "Nach Elfmeterschießen" evaluation | `mycoolfriendgroup` | Yes |
| `KICKTIPP_NAME_OF_90M_COMPETITION` | The name of the competition you want to tip for that uses the "Nach 90 min" evaluation | `mycoolfriendgroup` | No |
| `KICKTIPP_NAME_OF_NV_COMPETITION` | The name of the competition you want to tip for that uses the "Nach Verlängerung" evaluation | `mycoolfriendgroup` | No |
| `KICKTIPP_NAME_OF_NE_COMPETITION` | The name of the competition you want to tip for that uses the "Nach Elfmeterschießen" evaluation | `mycoolfriendgroup` | No |
| `KICKTIPP_HOURS_UNTIL_GAME` | The script will tip games which start in the next x hours | `24` | No |
| `LOG_LEVEL` | The log level of the script | `INFO` | Yes |
| `ZAPIER_URL` | The URL of your Zapier Webhook | `https://hooks.zapier.com/hooks/catch/123456/abcdef/` | No |
| `NTFY_URL` | The URL of your NTFY Webhook | `https://ntfy.your-domain.com` | No |
| `NTFY_USERNAME` | The username for your NTFY Webhook | `username` | No |
| `NTFY_PASSWORD` | The password for your NTFY Webhook | `password` | No |
| `IMAGE_NAME` | The image used for local builds | `tillbrodbeck/kicktipp-bot-serverless` | No |

## Notifications

If you want to receive a notification when the script tips for a match, you can use the Zapier or NTFY integration.

### Zapier

Please create a Zapier Account and set up the following Trigger: Custom Webhook. Please also make sure you set the ENV Variable `ZAPIER_URL` to the URL of your custom webhook. Then you can set up actions like sending an email or a push notification.

### NTFY

Set up your [ntfy](https://github.com/binwiederhier/ntfy?tab=readme-ov-file) server and set the ENV Variables `NTFY_URL`, `NTFY_USERNAME` and `NTFY_PASSWORD` to the values of your server. Create the topic `kicktipp-bot` and subscribe to it. Then you will receive a notification when the script tips for a match.

## Credits
Thank you to [Anton Engelhadt](https://github.com/antonengelhardt) for his [kicktipp-bot](https://github.com/antonengelhardt/kicktipp-bot) which inspired me to write this script.
