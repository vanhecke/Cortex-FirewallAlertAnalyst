# FirewallAlertAnalyst

A standalone worked example: one agent that triages a firewall alert end to end, built to
exercise every Agentix content type and every action capability the demisto-sdk supports.

## The agent

`firewall-alert-analyst-agent` follows a four-step procedure: score the alert deterministically,
pull only the traffic that answers a stated question, judge it with the score as evidence,
and record one verdict. It never recommends containment.

## Naming convention

Every content item ends its id with a token naming its type, so the type is readable
anywhere the item is mentioned - a flat tenant listing, an `underlyingcontentitem` block,
a conversation. The id is the display name in PascalCase (kebab-case for agents and
skills, matching SDK convention) plus that token:

| Type | Token | Example |
| --- | --- | --- |
| AgentixAgent | `-agent` | `firewall-alert-analyst-agent` |
| AgentixSkill | `-skill` | `firewall-alert-triage-skill` |
| AgentixAction | `Action` | `ScoreFirewallAlertAction` |
| Script, Python | `Script` | `ScoreFirewallAlertScript` |
| Script, `isllm: true` | `Prompt` | `TriageFirewallAlertPrompt` |
| Collection | `Collection` | `FirewallTriageWorkedAlertsCollection` |

The point is the action-to-underlying-item pair. `ScoreFirewallAlertAction` and
`ScoreFirewallAlertScript` share a stem and differ only in the token, so which is which
is obvious. The earlier names - action `ScoreFirewallAlert` backed by script
`FirewallAlertScore` - were word-order swaps of each other and got mixed up in practice.

Directory and file names follow the id: `AgentixActions/<Id>/<Id>.yml`, plus
`<Id>_test.yml` for actions and `<Id>_skill.md` / `<Id>_systeminstructions.md` where the
SDK requires a sidecar.

Display names stay plain prose - `Score Firewall Alert`, `Firewall Alert Analyst` - and
carry no type token. Display and `description` are the agent-facing surface the model
reasons over; decoration there is noise. Skill bodies and instructions refer to steps by
display name for the same reason, and use `<action=Id>` tokens where a real reference is
wanted.

## What each file is here to demonstrate

| Path | Capability |
| --- | --- |
| `AgentixAgents/firewall-alert-analyst-agent/` | every agent field: `color`, `visibility`, `conversationstarters`, `builtinactions`, `autoenablenewactions`, `roles`, `sharedwithroles`, `actionids`, `skillids`, `collectionids`, plus the required `_systeminstructions.md` (AG110) |
| `AgentixActions/SearchFirewallLogsAction/` | `underlyingcontentitem.type: command`, `requiresuserapproval`, `defaultvalue`, output `disabled` |
| `AgentixActions/GetFirewallSearchResultsAction/` | `type: command`, polling discipline in `fewshots` |
| `AgentixActions/ScoreFirewallAlertAction/` | `type: script`, and the full arg-flag set: `isgeneratable`, `hidden`, `disabled`, `defaultvalue` |
| `AgentixActions/DraftEscalationNoteAction/` | `isgeneratable` true on the prose args and false on the identifiers - and the live result that the flag does not enforce that split (see below) |
| `AgentixActions/TriageFirewallAlertAction/` | `type: prompt` - an LLM step with no Python behind it, wrapping `TriageFirewallAlertPrompt` |
| `AgentixActions/GetCaseDetailsAction/` | `type: command` bound with `_any_` to a platform command (`core-get-cases`) rather than to an integration by name |
| `AgentixActions/BlockIpAction/` | `type: playbook` - wraps `Block IP - Generic v3`. The web UI cannot author this: building an action there offers only commands and scripts, so a playbook-backed action has to come from a pack |
| `*/<Action>_test.yml` | AgentixActionTest (AG118), in both `any_of` and `sequence` modes |
| `AgentixSkills/firewall-alert-triage-skill/` | the skill body plus `<action=Id>` reference tokens (AG111) |
| `Collections/FirewallTriageWorkedAlertsCollection/` | a knowledge collection handle |
| `Scripts/ScoreFirewallAlertScript/` | a split `.yml` + `.py` Python automation |
| `Scripts/TriageFirewallAlertPrompt/` | `isllm: true` with `systemprompt`, `userprompt`, `model` and `promptConfig` |

That covers `command`, `script`, `prompt` and `playbook`. The fifth `underlyingcontentitem`
type, `internal`, is deliberately not shipped - see below.

The escalation codes `DraftEscalationNoteAction` needs exist ONLY in the collection - not
in the action, its fewshots, or the skill body. That is on purpose: it makes the pack a
live test of whether collection knowledge is reachable, and on current tenants it is not.
The agent should say it cannot find the list and ask. If it produces a code anyway, it
invented one, and the backing script rejects it.

## Server constraints the SDK does not encode

Found by deploying this pack to a live tenant. Each one validates clean and then fails
on the server, so the SDK will not warn you.

**`type: internal` does NOT mean "an action with nothing behind it".** It means "a platform
builtin, named by `command`" - and you cannot author the builtin. The pack briefly shipped
a `RecordFirewallVerdict` internal action on the theory that it would make the agent emit a
typed closing statement with no automation behind it. Every check passed and it did nothing.
What gives it away is that the server REWRITES the item on upload, replacing whatever `id`
and `name` you sent with the `_builtin_` sentinel and keeping only your `command`:

```json
"underlyingContentItem": {"id": "_builtin_", "name": "_builtin_",
                          "type": "internal", "command": "RecordFirewallVerdict"}
```

Real builtins name a handler the platform implements, in lowerCamelCase - the tenant has
six, among them `CortexRunXQLQuery` -> `runXQLQuery`, `CortexUpdateCase` -> `setCase`,
`EnrichIndicators` -> `enrichIndicators`. `RecordFirewallVerdict` was not one, so the action
pointed at a handler that does not exist.

Nothing catches this. The schema marks `command` optional, so omitting it fails the whole
pack on the server (`missing UnderlyingContentItem.Command for item type [internal]`,
`101801`) but supplying an invented one passes. GR110 `continue`s on `internal` before it
resolves anything. And `live` is worse than useless here: it is derived from
`state.errorCode` being empty, and since the server resolves nothing for `internal`, no
error can ever be raised - a dead action reports healthy. Do not author `internal` actions.

**A prompt (`isllm: true`) script needs a `model`.** `promptConfig` carries
`temperature` / `maxOutputTokens` / `webSearch` but has no field naming the LLM, and the
SDK validator is satisfied by `promptConfig` alone. Without `model` the action registers,
reports `live`, and returns HTTP 500 when invoked.

**A prompt script needs exactly one output.** `'Outputs' attribute must have 1 value (52)`.

**`temperature` is not accepted by every model.** The tenant's model list advertises
per-model `supportedParams`: `claude-opus-4-8` takes `maxTokens` / `stopSequences` /
`thinking` / `outputConfig` but NOT `temperature`; only `claude-sonnet-4-6` takes it.
Setting a parameter the chosen model does not support is a 500.

**An agent using LLM-backed actions wants `InvokeLLM` in `builtinactions`.** 11 of the 14
agents shipped on the tenant carry it; it is the only builtin they share.

**A pack-carried Collection is a dangling reference.** The strict model rejects `content`,
`body`, `documents`, `text`, `files` and `knowledge`, so a pack can only carry `name` and
`description` - and the upload registers the id on the agent
(`systemKnowledgeCollectionIds`) while creating no collection object:
`GET /xsoar/agentix/knowledgecollections` returns `[]`. The agent duly calls its
`QueryUserKnowledge` builtin and gets `references: []`. The description is NOT retrievable
content. Real documents have to be created tenant-side; `POST /xsoar/agentix/knowledgecollection`
is the likely route (it exists - GET returns 405). UNRESOLVED.

**`isgeneratable: false` does not stop the agent generating the argument.** Tested live on
`DraftEscalationNoteAction`: `escalation_code` is marked `isgeneratable: false`, and the
agent supplied `FW-ESC-4480` unprompted. Treat the flag as a marker for "this field is
meant to be LLM-authored", not as a gate. Enforce in the backing script instead. Note also
that this action cannot demonstrate lookup-versus-invention as built: the four valid codes
appear in the arg description, the fewshots AND the skill body, so the model reads them out
of its own context and never has to consult anything.

**`<action=Id>` tokens in a skill body are not rewritten by `upload`.** The preparer
resolves them through the content graph, which `upload` does not populate, so every id is
reported unresolved and the body ships with the literal token text. Whether the runtime
does anything with the resolved form is UNVERIFIED.

**You cannot read content back to check any of this.** `systemInstructions` is returned
encrypted (`{MULAN}...`), and there is no endpoint for skills, collections or prompts -
only `/xsoar/agentix/agents`, `/actions` and `/knowledgecollections` respond.

**Server support varies by tenant version.** On an older tenant the prompt-backed action
installed dead (`underlying content item ... of type [prompt] was not found`) and the
agent object had no `skillIds` or `systemKnowledgeCollectionIds` fields at all. The same
pack works on a current tenant. Ours was the only prompt-backed and only `internal` action
among 130 on that tenant, and the only agent using a collection - these paths are not
exercised by shipped content.

## Working on it

Requires [demisto-sdk](https://github.com/demisto/demisto-sdk) and a Cortex XSIAM tenant.
Run from the repository root, not from this directory.

```bash
export DEMISTO_BASE_URL="https://api-<tenant>.xdr.<region>.paloaltonetworks.com"
export DEMISTO_API_KEY="<key>"
export XSIAM_AUTH_ID="<auth id>"

demisto-sdk validate -i Packs/FirewallAlertAnalyst --config-path validation_config.toml
demisto-sdk upload   -i Packs/FirewallAlertAnalyst -z --marketplace platform
```

`--config-path` is not optional in practice: the SDK's default config selects no agentix
rule whatsoever. See AGENT_SPEC.md section 13.

Ids are identity on a tenant. If you rename one, uninstall the pack before re-uploading or
you will get the old and new objects side by side:

```
POST /xsoar/contentpacks/installed/delete   {"IDs": ["FirewallAlertAnalyst"]}
```

External dependencies: the Cortex XQL integration (`xdr-xql-generic-query`,
`xdr-xql-get-query-results`), `Cortex Core - Platform` (`core-get-cases`), and the
`Block IP - Generic v3` playbook. The two `mcp_...` entries in the agent's `actionids`
resolve only where a matching Generic MCP instance exists - see the repository README.
