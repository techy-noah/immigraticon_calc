import os
import json
import logging
from typing import Any

from openai import OpenAI

from .ai_context import AIContextBuilder

logger = logging.getLogger(__name__)


class AIReportService:
    def __init__(self):
        self.client = None
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        self.context_builder = AIContextBuilder()

    def generate_report(self, submission: Any, scores: dict, strengths: list, gaps: list) -> str | None:
        if not self.client:
            logger.warning("OpenAI client not initialized. Set OPENAI_API_KEY environment variable.")
            return None

        ai_context = self.context_builder.prepare_ai_context(submission, scores)
        prompt = self._build_prompt(submission, scores, strengths, gaps, ai_context)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a thoughtful immigration consultant helping researchers and professionals understand their EB1A and EB2 NIW petition potential. You write helpful, honest reports that empower candidates to make informed decisions. Your tone is professional, encouraging, and grounded — you help people see both their strengths and their path forward. You NEVER use fear tactics or overpromise outcomes. You believe that with the right guidance, many qualified candidates can strengthen their cases."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6,
                max_tokens=2800
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def _build_prompt(self, submission: Any, scores: dict, strengths: list, gaps: list, ai_context: dict) -> str:
        raw = submission.raw_answers or {}
        total_score = scores.get('total_score', 0)
        max_score = scores.get('max_total', 115)
        petition_rec = ai_context.get('petition_recommendation', {})
        recommendation = petition_rec.get('recommendation', 'TBD')

        context_json = json.dumps(ai_context, indent=2)

        prompt = f"""Write a personalized immigration assessment report for {submission.full_name} based ONLY on the structured data provided.

== TONE AND STYLE ==
- Write like a knowledgeable friend who happens to be an immigration expert
- Be honest about gaps without being discouraging
- Use phrases like "In our experience..." and "What we typically see..."
- Frame gaps as opportunities: "These areas, when addressed, can significantly strengthen..."
- Subtle urgency: "These gaps should ideally be addressed before filing..."
- Never say "You will be denied" or "You have no chance"
- Never promise approval or guarantee outcomes

== STRICT RULES ==
1. Use EXACT scores and values from the structured context
2. Reference specific categories, numbers, and data provided
3. Do NOT invent or assume any data not in the context
4. Do NOT mention "structured context" or "JSON" in your output
5. Output MUST align with the petition_recommendation
6. Length: 650-900 words

== CANDIDATE PROFILE ==
Name: {submission.full_name}
Petition Interest: {submission.petition_type_interest}
EB1A Readiness: {submission.eb1_eligibility or 'Assessment pending'}

== STRUCTURED DATA ==
{context_json}

== REPORT SECTIONS ==

## YOUR EB1/EB2 ASSESSMENT — {total_score} OUT OF {max_score}

Open with a clear verdict. Recommend: {recommendation}. Be direct but warm.

---

## WHERE YOU STAND

In our experience, profiles like yours tend to be [EB1A/EB2 NIW/both — based on recommendation]. 

Discuss 2-3 specific strengths with actual numbers. Then acknowledge 1-2 key areas where focused effort can make a real difference. End with a forward-looking sentence about their path.

---

## YOUR STRONGEST ASSETS

For each strength (use exact scores from context):
- [Category name]: [Score]/[Max] — Explain what this means in plain terms
- Why USCIS gives weight to this
- One specific thing to document well

Example: "Citations (15/15): With 15 citations, your work shows meaningful peer recognition. This is one of the most heavily weighted criteria..."

---

## CRITICAL AREAS TO ADDRESS

Frame these as opportunities, not failures:
For each gap:
- [Category]: Currently at [score]/[required] — Here's what this means
- Why this matters for your petition
- These areas should ideally be addressed before filing, but we can discuss strategy

Example: "Media Coverage (0/10): This is currently a gap, but it's also an opportunity. Building visibility in your field through interviews, press, or industry coverage can strengthen your national recognition claim."

---

## YOUR BEST PATH FORWARD

{recommendation}: [Use the reasoning from context]

In our experience, applicants with this profile often find that [specific insight based on their data]. A consultation can help map out the most efficient path forward.

---

## YOUR ACTION ROADMAP

Prioritized steps from the context:
- **[Priority Level]** [Area]: [Specific action]

Make it feel achievable, not overwhelming.

---

## WHAT TO KNOW BEFORE FILING

Share relevant risks from context, but frame them as considerations:
- "RFEs are common in cases where..."
- "In our experience, applicants who address [X] first tend to have smoother processes..."

Be factual, not alarming.

---

## LET'S DISCUSS YOUR STRATEGY

Warm closing paragraph:
- Acknowledge they've done good work to get here
- Mention what a consultation would help with (based on their specific gaps)
- Something like: "I'd be happy to walk through your specific situation and share what we typically recommend in cases like yours. A brief conversation can clarify whether to pursue [EB1A/EB2] now or build your profile first."

Keep it under 50 words. No pressure — just an invitation.

== END ==
"""
        return prompt
