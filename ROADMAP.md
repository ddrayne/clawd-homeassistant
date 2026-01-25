# Roadmap & Enhancement Plan

This document outlines planned features, optimizations, and improvements for the Clawd Home Assistant integration based on Clawdbot Gateway capabilities.

## 🔥 High Priority Features

### 1. Streaming Responses
**Status:** Planned  
**Complexity:** Medium  
**Impact:** High

The Clawdbot Gateway supports WebSocket streaming for real-time response delivery.

**Benefits:**
- Faster perceived response time (start speaking while generating)
- Better UX for long responses
- Can begin TTS generation before full response completes
- Visual feedback ("Clawd is thinking...")

**Implementation:**
- Switch from buffered to streaming WebSocket connection
- Process tokens as they arrive
- Start TTS generation on sentence boundaries
- Add streaming indicator to HA UI

**Technical Details:**
```python
# Current: Wait for complete response
response = await self._send_message(user_input)

# Proposed: Stream tokens
async for token in self._stream_message(user_input):
    buffer += token
    if sentence_complete(buffer):
        yield buffer
        buffer = ""
```

### 2. Sub-Agent Task Spawning
**Status:** Planned  
**Complexity:** Medium  
**Impact:** High

Leverage `sessions_spawn` for background task execution.

**Use Cases:**
- "Research restaurants and email me the results"
- "Check flight status every hour and notify me of changes"
- "Monitor my inbox for messages from [person] and alert me"
- Complex multi-step tasks that shouldn't block voice response

**Implementation:**
- Add `clawd.spawn_task` service
- Accept task description, optional cleanup policy
- Return task ID immediately
- Set up callback mechanism for completion notifications
- Integrate with HA notifications/automations

**Example Service Call:**
```yaml
service: clawd.spawn_task
data:
  task: "Research Edinburgh restaurants with good reviews and email me a list"
  cleanup: "delete"
  notify_on_complete: true
```

### 3. Model Selection & Reasoning Mode
**Status:** Planned  
**Complexity:** Low  
**Impact:** Medium

Expose gateway's model selection and thinking capabilities.

**Features:**
- Per-request model override (fast vs. powerful)
- Thinking/reasoning mode control (off/low/medium/high)
- Auto-detect complex queries and enable reasoning
- Cost-aware model selection

**Configuration:**
```yaml
# Integration options
model_strategy: "auto"  # auto, fast, balanced, powerful
thinking_mode: "auto"   # off, low, medium, high, auto
```

**Auto-Detection:**
- Simple queries → sonnet (fast)
- "Explain", "analyze", "compare" → opus + high thinking
- Cost tracking per model

### 4. Session Management
**Status:** Planned  
**Complexity:** Low  
**Impact:** Medium

Dynamic session switching and multi-session support.

**Features:**
- Service to switch active session
- Multiple conversation entities for different sessions
- Session history access (`sessions_history`)
- Cross-session message sending (`sessions_send`)

**Use Cases:**
- Separate work vs. personal assistant sessions
- Family members with individual sessions
- Context isolation (home automation vs. general queries)

## 🚀 Medium Priority Features

### 4. Memory Integration
**Status:** Planned  
**Complexity:** Medium  
**Impact:** Medium

Leverage Clawdbot's `memory_search` for context-aware responses.

**Benefits:**
- Pull relevant past conversations
- Personalized responses based on preferences
- Cross-platform context ("What did I ask you on Telegram?")

**Implementation:**
- Pre-query memory search for relevant context
- Inject context into conversation prompt
- Expose as optional feature (privacy considerations)

### 5. Cron & Reminder Integration
**Status:** Planned  
**Complexity:** Medium  
**Impact:** High

Integrate with gateway's cron system for scheduled tasks.

**Features:**
- Voice-activated reminders
- Recurring task scheduling
- Integration with HA automations
- "Remind me to check the oven in 20 minutes"

**Implementation:**
- `clawd.schedule_reminder` service
- Parse natural language time expressions
- Fire HA events on reminder trigger
- Support one-time and recurring reminders

## ⚡ Performance Optimizations

### 1. Connection Pooling & Keepalive
**Status:** Planned  
**Complexity:** Low  
**Impact:** Medium

Replace periodic health checks with persistent WebSocket + heartbeat.

**Current:** HTTP health check every 60s  
**Proposed:** Persistent WebSocket with ping/pong keepalive

**Benefits:**
- Lower latency on first request
- Reduced connection overhead
- Immediate failure detection
- More reliable in poor network conditions

### 2. Response Caching
**Status:** Planned  
**Complexity:** Low  
**Impact:** Low-Medium

Cache identical queries for short duration.

**Strategy:**
- Cache responses for 30-60 seconds
- Hash query + context for cache key
- Bypass cache for explicit "new" queries
- Size limit to prevent memory issues

**Use Cases:**
- Repeated "What's the weather?" → instant response
- Same question from multiple family members
- Accidental duplicate voice triggers

### 3. Parallel Query Processing
**Status:** Planned  
**Complexity:** Medium  
**Impact:** Medium

Support compound queries with parallel execution.

**Examples:**
- "What's the weather AND check my calendar"
- "Email summary AND upcoming meetings"

**Implementation:**
- Parse compound queries (AND, ALSO, THEN)
- Fire independent queries in parallel
- Aggregate responses
- Gateway already supports concurrency

### 4. Adaptive Timeout Handling
**Status:** Planned  
**Complexity:** Low  
**Impact:** Medium

Auto-adjust timeout based on query complexity.

**Strategy:**
- Quick queries: 10s timeout
- Tool-using queries: 30s timeout
- Research/complex: 60s+ timeout
- Learn from historical response times

**Detection:**
- Keyword-based (simple heuristics)
- Response time history per query type
- Explicit timeout override in advanced cases

## 📊 Observability & Diagnostics

### 1. Usage & Cost Tracking
**Status:** Planned  
**Complexity:** Low  
**Impact:** Medium

Expose `session_status` metrics as HA sensors.

**Sensors:**
- `sensor.clawd_tokens_used`
- `sensor.clawd_estimated_cost`
- `sensor.clawd_queries_today`
- `sensor.clawd_avg_response_time`

**Benefits:**
- Monitor AI usage
- Cost awareness (paid models)
- Performance tracking
- Usage patterns

### 2. Enhanced Diagnostics
**Status:** Planned  
**Complexity:** Low  
**Impact:** Low

Expand diagnostic data for troubleshooting.

**Additional Data:**
- WebSocket connection stats
- Query latency breakdown
- Error frequency/types
- Memory usage
- Active sessions list

## 🎯 Quick Wins (Easy Implementations)

1. **`clawd.spawn_task` service** - Async task spawning (2-4 hours)
2. **Thinking mode selector** - Config option for reasoning (1 hour)
3. **Model strategy** - Fast/balanced/powerful presets (2 hours)
4. **Session selector service** - Dynamic session switching (1-2 hours)
5. **Usage sensor** - Basic token/cost tracking (2-3 hours)

## 🔮 Future Considerations

### Advanced Features
- Multi-turn conversation optimization
- Voice activity detection integration
- Custom wake word support
- Proactive notifications based on memory/context
- Integration with HA's LLM conversation API
- Voice profile switching (per-user sessions)

### Edge Cases
- Offline mode / local model fallback
- Rate limiting and backpressure
- Multi-language support
- Privacy controls (data retention, memory opt-out)

## Implementation Priority

### Phase 1: Core Enhancements (v1.1.0)
- [ ] Streaming responses
- [ ] Model selection
- [ ] Thinking mode control
- [ ] Basic usage sensors
- [ ] Session management
- [ ] Connection pooling

### Phase 2: Advanced Features (v1.2.0)
- [ ] Sub-agent spawning
- [ ] Memory integration

### Phase 3: Optimization & Polish (v1.3.0)
- [ ] Response caching
- [ ] Parallel queries
- [ ] Adaptive timeouts
- [ ] Enhanced diagnostics

### Phase 4: Future Features (v2.0.0)
- [ ] Cron integration
- [ ] Proactive notifications
- [ ] Voice profiles
- [ ] Advanced observability

## Contributing

Contributions are welcome! If you'd like to implement any of these features:

1. Open an issue to discuss the approach
2. Reference this roadmap in your PR
3. Update the roadmap status when starting work

## Feedback

Have ideas for other enhancements? Open an issue with the `enhancement` label!

---

*Last Updated: 2026-01-25*  
*Integration Version: 1.0.0*
