# Clawd Voice Assistant for Home Assistant

<p align="center">
  <img src="custom_components/clawd/icon.png" alt="Clawd Icon" width="128" height="128">
</p>

Integrate [Clawdbot](https://docs.clawd.bot/) with Home Assistant's voice control system, enabling your voice assistant to be powered by Claude through Clawd.

Use Claude as your conversation agent in Home Assistant, bringing natural language understanding and intelligent responses to your smart home voice commands and Assist interface.

## Features

- **Direct WebSocket Integration**: Real-time connection to Clawdbot Gateway
- **Universal Language Support**: Works with any language Claude supports
- **Smart TTS Processing**: Configurable emoji stripping for clean text-to-speech output
- **Flexible Authentication**: Token-based auth with SSL/TLS support
- **Reliable Connection**: Automatic reconnection with graceful error handling
- **Customizable Sessions**: Route conversations to different Clawdbot sessions
- **Fast Responses**: Typical response time of 5-10 seconds for most queries
- **Easy Configuration**: Simple UI-based setup through Home Assistant

## Requirements

- Home Assistant 2024.1.0 or later
- Python 3.11 or later
- A running Clawdbot Gateway (local or remote)
- Gateway token (for non-localhost connections)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Add"
7. Search for "Clawd Voice Assistant"
8. Click "Download"
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/clawd` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

### Setting Up the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Clawd Voice Assistant"
4. Enter your Gateway connection details:
   - **Host**: Gateway hostname or IP address (e.g., `gateway.example.com` or `192.168.1.100`)
   - **Port**: Gateway port (default: `18789`)
   - **Gateway Token**: Your authentication token (leave empty for localhost without authentication)
   - **Use SSL**: Check this for `wss://` connections (recommended for remote connections)
   - **Agent Timeout**: Maximum time to wait for agent response in seconds (default: 30)
   - **Session Key**: Clawdbot session to use (default: `main` - the standard direct-chat session)
   - **Strip emojis from TTS speech**: Remove emojis from spoken responses (default: enabled)

5. Click **Submit**

### Configuring Voice Assistant

1. Go to **Settings** → **Voice Assistants** → **Assist**
2. Select your preferred voice assistant
3. Under **Conversation agent**, select **Clawd**
4. Save changes

## Usage

Once configured, your Home Assistant voice assistant will use Clawd to process conversations:

- **Voice Commands**: Use any Home Assistant voice interface (mobile app, voice satellites, etc.)
- **Assist Interface**: Type or speak to Claude through the Home Assistant UI
- **Natural Conversations**: Ask questions, get explanations, have multi-turn conversations
- **All Requests**: Sent securely to your Clawdbot Gateway's agent endpoint

### Example Interactions

Claude can handle a wide variety of requests beyond typical voice assistant commands:

**Information & Explanations:**
- "What's the weather like today?"
- "Explain how solar panels work"
- "Who sent me a telegram message?"

**Conversational:**
- "Who are you?"
- "Tell me a joke"
- "What can you help me with?"

**Math & Calculations:**
- "What's 2 plus 2?"
- "Convert 100 fahrenheit to celsius"
- "Calculate the area of a circle with radius 5"

**General Knowledge:**
- "What year did the first moon landing happen?"
- "Explain photosynthesis"
- "What's the capital of Japan?"

**Note**: Claude responds with natural, conversational language. For home automation commands, you may want to use Home Assistant's built-in intents alongside Claude for the best experience.

## Remote Gateway Setup

If your Clawdbot Gateway is running on a different machine, you have two options:

### Option 1: Direct Connection (Recommended with SSL)

Configure the integration with your Gateway's hostname/IP and enable SSL:
- Host: `gateway.example.com` or IP address
- Port: `18789`
- Use SSL: ✓ (enabled)
- Gateway Token: Required

### Option 2: SSH Tunnel

Set up an SSH tunnel separately and connect via localhost:

```bash
# Set up SSH tunnel (run this command on your Home Assistant machine)
ssh -N -L 18789:localhost:18789 user@gateway-host
```

Then configure the integration:
- Host: `127.0.0.1`
- Port: `18789`
- Gateway Token: (Optional)

## Troubleshooting

### Connection Errors

**Cannot reach Clawd Gateway:**
- Check that the Gateway is running: `clawdbot status`
- Verify the host and port are correct
- Check firewall rules
- For remote connections, ensure SSL is enabled if required

**Authentication failed:**
- Verify your token is correct
- Check Gateway token configuration: `echo $CLAWDBOT_GATEWAY_TOKEN`
- For localhost connections without a token, leave the token field empty

**Response timeout:**
- Agent execution is taking longer than the configured timeout (default: 30 seconds)
- Typical response time is 5-10 seconds for most queries
- Complex questions may take longer (up to 30+ seconds)
- Increase the timeout setting in integration options if needed
- Check Gateway logs for issues

### Performance Issues

**Slow responses:**
- Most queries respond in 5-10 seconds
- Complex reasoning or long responses may take 15-30+ seconds
- This is normal for AI agent processing
- Consider increasing the timeout for complex queries

**Connection drops:**
- Check network stability
- The integration will automatically reconnect
- Check Gateway logs for any issues

## Limitations

- **Response time**: Typical queries take 5-10 seconds. While faster than early AI assistants, this is still slower than traditional rule-based voice assistants (1-2 seconds)
- **Streaming**: Responses are buffered and returned complete (no streaming TTS support during generation)
- **Home Automation**: Best used alongside Home Assistant's native intents for device control. Claude excels at information, conversation, and complex queries rather than simple "turn on the lights" commands
- **Context**: Conversation history is managed by Home Assistant's ChatLog (persists across queries within a conversation)

## Security

- **Token storage**: Tokens are encrypted at rest by Home Assistant
- **SSL/TLS**: Recommended for all remote connections
- **SSH tunnels**: Can be used as an alternative to direct connections
- **Non-SSL warning**: The integration warns when connecting to non-localhost without SSL

## Advanced Configuration

### Updating Settings

You can update the Gateway connection settings without removing the integration:

1. Go to **Settings** → **Devices & Services**
2. Find the **Clawd Voice Assistant** integration
3. Click **Configure**
4. Update settings as needed
5. Click **Submit**

### Session Keys

The **Session Key** setting allows you to route Home Assistant conversations to specific Clawdbot sessions:

- **Default (`main`)**: The standard direct-chat session - conversations appear in your main Clawdbot session
- **Custom sessions**: Use a different session key to organize Home Assistant conversations separately
- **Use cases**:
  - Keep Home Assistant conversations isolated from other Clawdbot interactions
  - Route to different agents if you have multiple configured
  - Organize conversations by purpose (e.g., `home-assistant`, `automation`, etc.)

To use a custom session, simply enter the desired session key in the integration configuration.

### Emoji Stripping

The **Strip emojis from TTS speech** option controls whether emojis are removed from spoken responses:

- **Enabled (default)**: Emojis are removed from text-to-speech output for cleaner speech
  - Example: "I'm Claude 🦞" → Speaks "I'm Claude"
  - Emojis remain visible in the conversation history
- **Disabled**: TTS attempts to read emojis (may sound awkward depending on your TTS engine)
  - Example: "I'm Claude 🦞" → Speaks "I'm Claude lobster emoji"

**When to disable:**
- You have a high-quality TTS engine that handles emojis well
- You prefer emoji descriptions to be spoken
- You're using the integration primarily through text (Assist interface) rather than voice

You can change this setting anytime in **Settings** → **Devices & Services** → **Clawd** → **Configure**.

### Multiple Gateways

You can add multiple Gateway connections if needed:
- Each Gateway requires a unique host:port combination
- Configure multiple conversation entities
- Select different agents in different voice assistant configurations

## License

Apache License 2.0 - See LICENSE file for details

## Credits

- Built for [Clawdbot](https://docs.clawd.bot/) by Anthropic
- Home Assistant conversation entity integration

## Support

- Report issues: [GitHub Issues](https://github.com/ddrayne/clawd-homeassistant/issues)
- Clawdbot documentation: [https://docs.clawd.bot/](https://docs.clawd.bot/)
- Home Assistant community: [https://community.home-assistant.io/](https://community.home-assistant.io/)
