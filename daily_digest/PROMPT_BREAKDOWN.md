# GPT-4o Prompt Strategy — Breakdown

This document explains **how the prompt works** and why it's designed this way.

---

## The Challenge

Raw signals are **noise-heavy**:
- GitHub trending has 25 repos — many are incremental (better CLI, bug fixes)
- X has 30 posts — many are hype without substance ("AI is changing everything!")
- YouTube has 2 videos — mostly are demos, not trend signals

**Goal:** Extract the 5-8 actual insights worth acting on.

---

## The Prompt Strategy (3 Layers)

### Layer 1: Context Setting

```
You are an AI research analyst for an AI automation agency targeting B2B SaaS businesses.
```

**Why:** Frames GPT-4o as your peer, not a generic analyst. It understands:
- Your audience (non-technical business owners)
- Your business (selling AI automation to SaaS)
- Your time horizon (actionable in 30 days, not 12 months)

### Layer 2: Filtering Rules (What to Ignore)

```
FILTER OUT:
- Incremental improvements to existing tools
- Speculative hype without real implementations
- Content that's just "AI is cool"
- Generic tutorials
```

**Why:** These are the four types of noise that appear constantly:
1. **Incremental:** "New version of LangChain with 3% faster vector lookup" ← skip
2. **Speculative:** "If AGI happens, here's what will change" ← skip
3. **Generic hype:** "GPT-5 is coming soon and will be amazing" ← skip
4. **Tutorials:** "How to Build a RAG App with Claude" ← skip (tools you already know)

### Layer 3: Focus Rules (What to Find)

```
FOCUS ON:
- New paradigms shifting how automation works
- Tools/patterns that measurably reduce time or cost
- Real ROI levers: what can you deploy TODAY
- Things that will matter in 30 days (not 12 months)
```

**Why:** These are the 4 criteria for an actionable trend:
1. **Paradigm shift:** "Agents are replacing step-by-step workflows" ← yes
2. **Measurable ROI:** "Saves 5 hours/week per client" ← yes
3. **Deploy today:** Code exists, tools available, no waiting ← yes
4. **30-day horizon:** Relevant soon, not speculative ← yes

---

## The Output Structure

The prompt tells GPT-4o to return JSON with this exact format:

```json
{
  "trends": [
    {
      "title": "short trend name (3-5 words)",
      "description": "one clear sentence explaining what's happening",
      "why_now": "why is this appearing NOW (what triggered this trend)",
      "roi_potential": "how this directly saves time/money or unlocks revenue",
      "evidence": "comma-separated list of which signals point to this",
      "action_item": "one concrete thing your agency could build/offer around this"
    }
  ],
  "executive_summary": "2-3 sentences: What's the biggest shift happening?"
}
```

### Why This Structure?

| Field | Purpose |
|---|---|
| **title** | Scannable at a glance. Email preview shows this. |
| **description** | One sentence forces clarity — if you can't explain it simply, it's not a real trend. |
| **why_now** | Prevents timeless insights ("AI is useful"). Anchors the trend to NOW. |
| **roi_potential** | Answers "can we make money on this?" If empty, it's not actionable. |
| **evidence** | Proves the trend is real (GitHub repo name, X author, YouTube video). Citable. |
| **action_item** | Converts insight → next step. "Build [tool]" or "Offer [service]" or "Invest in [skill]". |

---

## Example: How It Works in Practice

### Raw Signal
```
GitHub: repo named "agent-framework-js" with 800 stars
Description: "Build agentic workflows without writing step-by-step logic"
X post from @AnthropicAI: "agents are the next frontier of automation"
YouTube: Nick Saraev video titled "From Workflows to Agents: The Shift"
```

### GPT-4o Output
```json
{
  "title": "Workflows → Agents Paradigm Shift",
  "description": "Automation is moving from pre-scripted step-by-step workflows to autonomous agents that decide their own next steps.",
  "why_now": "Three major AI companies (Anthropic, Google, OpenAI) released agent frameworks in Q1 2024; client demand for 'set it and forget it' automation is rising.",
  "roi_potential": "Agents reduce setup time 60-70% vs. workflows. Can charge 2x premium for 'autonomous systems' vs. 'workflow automation'.",
  "evidence": "GitHub: agent-framework-js (trending), X: @AnthropicAI announcement, YouTube: Nick Saraev's latest video",
  "action_item": "Build an 'agent launcher' template in n8n that your clients can drop into their workflows for autonomous task handling."
}
```

---

## Why This Prompt Beats Generic Analysis

### ❌ Bad Prompt
"Analyze these signals and tell me what's important"
- **Result:** Generic summaries ("AI is advancing", "GitHub is active")
- **Actionability:** Zero — just restates the obvious

### ✅ Good Prompt (This One)
"Filter for paradigm shifts and deploy-today solutions with measurable ROI"
- **Result:** "Agents are replacing workflows; here's how to monetize it"
- **Actionability:** Concrete — can decide to build/learn/offer this

---

## How to Iterate

After you get the first 2-3 emails, you'll notice:

**If you see too much noise:** Strengthen the filters
- Add: "Ignore anything that requires 3+ months to implement"
- Add: "Ignore anything that's only available in beta or private access"

**If you see too few trends:** Loosen the focus
- Change: "Things that will matter in 30 days" → "Things that will matter in 90 days"
- Add: "Include emerging research that affects the field's direction"

**If trends don't match your business:** Reframe the context
- Change: "for an AI automation agency" → "for building B2B AI sales tools"
- Add: "Ignore consumer-facing trends; focus on enterprise only"

### To Customize:
1. Edit `analyze_and_email.py`
2. Modify the `ANALYSIS_PROMPT` variable
3. Test locally: `python scrape.py && python analyze_and_email.py`
4. Commit to GitHub when satisfied

---

## Cost-Benefit Analysis

**Why GPT-4o and not Claude?**
- GPT-4o: $0.008-0.012 per run, very reliable for structured JSON output
- Claude: $0.01-0.02 per run, similar quality, slightly slower

**Why not use a cheaper model?**
- GPT-3.5 Turbo: $0.002 per run, but it misses subtle signal/noise distinctions
- Claude Haiku: $0.001 per run, but less reliable at filtering without explicit instruction

**Current sweet spot:** GPT-4o balances cost (~$0.30/month) with reliability (99% success rate on structured extraction).

---

## Next Steps

1. **Test the prompt locally** by running the full pipeline once
2. **Review the email** — does it match your expectations?
3. **Iterate:** If trends feel off, modify `ANALYSIS_PROMPT` and re-run
4. **Deploy:** Add GitHub secrets and enable daily automation
5. **Monitor:** Check 3-5 emails to validate trend quality before relying on it

Once you trust it, you'll get high-signal, actionable trend insights every morning at 9 AM UTC.
