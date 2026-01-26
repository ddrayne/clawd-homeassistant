# Roadmap & Enhancement Plan

This document tracks release scope and future ideas for the Clawd Home Assistant integration.

## Release 1.2 (Beta) - Done

- Streaming responses with HA streaming fallback
- Persistent WebSocket connection with keepalive and reconnects
- Session selector in config flow + `clawd.set_session`
- Model override and thinking mode override
- Usage sensors (tokens, cost, message count)
- Background task spawning (`clawd.spawn_task`) with `clawd_task_complete` event
- Cron services (`clawd.cron_add`, `clawd.cron_remove`, `clawd.cron_run`)

## 2.0 Candidates (Backburner)

### Agent & Session Enhancements
- Session management expansions (multi-entity sessions, history, cross-session send)
- Memory search injection (optional pre-query context)
- Proactive notifications based on memory/context
- Voice profile switching (per-user sessions)
- Integration with HA's LLM conversation API

### Scheduling & Automation
- Natural language reminders (`clawd.schedule_reminder`)
- Cron job listing UI or sensors
- Event hooks for cron run outcomes

### Performance & Reliability
- Response caching
- Parallel query processing
- Adaptive timeouts

### Observability
- Advanced diagnostics (latency breakdown, error rates, connection stats)
- Additional usage sensors (queries today, average response time)
- Advanced observability dashboards

## Contributing

Contributions are welcome! If you'd like to implement any of these features:

1. Open an issue to discuss the approach
2. Reference this roadmap in your PR
3. Update the roadmap status when starting work

## Feedback

Have ideas for other enhancements? Open an issue with the `enhancement` label!

---

*Last Updated: 2026-01-25*  
*Integration Version: 1.0.1*
