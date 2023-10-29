# vps-manager
Work-in-progress bot to interact with a VPS through a discord bot.
The idea is to be able to have each VPS ip, useranme and passoword defined in a config file,
then you can "log-in" to any of these in a discord channel, and then exectute commands on the vps that is "logged-in"
in that channel.

# Available commands
- /login - Lets you select a predefined VPS from the config file
- /currentvps - Shows which vps is logged in the cvurrent channel, and the time until the "log-in" is valid for
- /vpsresources - Shows details about the vps, such as:
    - CPU Usage
    - Memory Usage
    - Disk Usage
    - Processes using most CPU (not fully working)

- /help - Shows available commands (incomplete)


## Requirements

- Python 3.8 or higher
- Discord bot token

## Setup Instructions

1. Ensure that Python is installed on your system. If not, you can download it from [Python's official website](https://www.python.org/downloads/).
   
2. Clone the bot repository to your local machine.

3. Open a terminal or command prompt, navigate to the bot's directory, and run the following command to install the required Python packages:

   ```sh
   pip install discord bson configparser asyncio asyncssh


## Configuration

1. Rename `config_example.ini` to `config.ini`.
2. Open `config.ini` and fill in the appropriate values for each field.
3. Save `config.ini`.

**Note: Never share your `config.ini` file with anyone as it contains sensitive information.**
. Replace the placeholder text with your bot's actual token, which can be obtained from the [Discord Developer Portal](https://discord.com/developers/applications).

## Running the bot locally
Run the bot by executing the Python file in the terminal or command prompt.
   
   ```sh
   python bot.py