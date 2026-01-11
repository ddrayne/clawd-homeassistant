# Clawd Voice Assistant for Home Assistant

Integrate [Clawdbot](https://docs.clawd.bot/) with Home Assistant's voice control system, enabling your voice assistant to be powered by Claude through Clawd.

## Features

- Direct integration with Clawdbot Gateway via WebSocket
- Universal language support
- Token-based authentication
- Automatic reconnection
- Configurable timeouts
- SSL/TLS support

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

5. Click **Submit**

### Configuring Voice Assistant

1. Go to **Settings** → **Voice Assistants** → **Assist**
2. Select your preferred voice assistant
3. Under **Conversation agent**, select **Clawd**
4. Save changes

## Usage

Once configured, your Home Assistant voice assistant will use Clawd to process conversations:

- Use voice commands via the Home Assistant mobile app
- Interact through the Assist interface in Home Assistant
- All requests are sent to your Clawdbot Gateway's agent endpoint

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
- Agent execution is taking longer than the configured timeout
- Increase the timeout setting in integration options
- Check Gateway logs for issues

### Performance Issues

**Slow responses:**
- Agent execution can take 10-30+ seconds depending on complexity
- This is normal for AI agent processing
- Consider increasing the timeout if needed

**Connection drops:**
- Check network stability
- The integration will automatically reconnect
- Check Gateway logs for any issues

## Limitations

- **Response time**: AI agent processing can take 10-30+ seconds, which is longer than typical voice assistants
- **Streaming**: Responses are buffered and returned complete (no streaming support)
- **Context**: Conversation history is managed by Home Assistant's ChatLog

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
