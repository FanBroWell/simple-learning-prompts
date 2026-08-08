# Hero Image Generation Prompt

## Positioning

**Emotional pain + before/after contrast + an immediately usable solution**

- Pain: the student searched for answers but still does not understand.
- Action: copy one prompt and send it together with the question.
- Transformation: AI teaches the concept like a patient tutor instead of merely revealing an answer.

## Image generation prompt

```text
Use case: ads-marketing
Asset type: 16:9 GitHub README hero and shareable project cover
Primary request: Create a premium editorial illustration for an open-source project that lets a student copy one prompt, attach a difficult homework question, and receive an AI explanation that feels like patient one-to-one tutoring. Tell a crystal-clear three-step story from left to right in one coherent scene.

LEFT — A natural-looking 12–14-year-old Chinese middle-school student with black hair and simple unbranded navy clothing sits alone at a desk, visibly stuck on a math problem in an open workbook. Cool gray-blue light, slightly tense but not exaggerated. A few abstract search panels suggest that looking up answers has not helped.

CENTER — Make the product action visually unmistakable. Show a large clean phone or tablet interface where an abstract prompt card is being copied into an AI chat together with a photographed homework problem. Use a recognizable copy icon, question-image thumbnail, and send arrow, but no readable text or letters. A clear flowing visual connector leads to the right.

RIGHT — Show the same Chinese child attentive and relieved, now learning from an online tutor-style AI interface. Inside a large screen, show a warm and friendly Chinese teacher-style avatar pointing to a clean whiteboard with three elements: step-by-step reasoning, one familiar real-life analogy, and one small check-question card. The interaction must feel like teaching and dialogue, not simply revealing an answer.

Style: polished modern editorial illustration with realistic human proportions, warm and credible, crisp shapes, subtle depth, soft natural lighting, suitable for GitHub and Chinese social media. Not a stock photo collage and not childish cartoon art.

Composition: 16:9 landscape intended for 1600x900. Compact three-part composition. Keep the Chinese child, prompt-copy action, and tutor screen relatively close to the center so the story remains understandable at thumbnail size. Leave a wide quiet band across the upper center for deterministic Chinese headline typography later.

Color: left side cool desaturated gray-blue; center clear blue; right side warm blue-green with a calm optimistic glow.

Constraints: the student must clearly be a Chinese child, not an adult and not Western. Keep the same child identity on both sides. No readable text, letters, Chinese characters, gibberish typography, logos, watermarks, branded UI, school badges, graduation caps, robots, humanoid robot teachers, neon cyberpunk visuals, or exaggerated emotions. Do not render any headline or labels; all wording will be added later.
```

## Deterministic typography

Chinese:

- Headline: `不是你学不会，是一直没人把它讲明白。`
- Subtitle: `把题目丢给 AI，让它用大白话、生活例子和“为什么”，一直讲到你懂。`
- Call to action: `一个模板，复制就能用`
- Steps: `搜了很多，还是不懂` → `题目 + Prompt 交给 AI` → `终于讲明白了`

English:

- Headline: `You are not bad at learning. It just was not explained clearly.`
- Subtitle: `Give AI the question and make it explain the plain-language idea, the why, and a real-life example—until it clicks.`
- Call to action: `One template. Copy and use it.`

## Output requirements

- Canvas: 1600 × 900, landscape PNG.
- Preserve the text-free generation as `hero-background.png`.
- Add exact Chinese text in `hero.png` and English text in `hero.en.png`.
- No AI-generated typography, logos, watermarks, or branded interfaces.
