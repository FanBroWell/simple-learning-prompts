# Hero Image Generation Prompt

## Positioning

**Show the result, not just the concept:** a student copies one reusable Prompt with a question and receives a complete teacher-like explanation.

- Pain: searched many answers, but still does not understand.
- Action: copy the Prompt and send it with the question.
- Visible outcome: AI explains the idea in plain language, gives the reason, uses a real-life analogy, solves it step by step, and checks understanding.

## Image generation prompt

```text
Use case: ads-marketing
Asset type: 16:9 GitHub README hero and Chinese social-media cover

Create a polished premium editorial illustration for an open-source AI learning prompt project. The image must clearly show not only the prompt input, but also the structured answer produced after using it.

COMPOSITION PRIORITY:
The RIGHT-SIDE AI answer dashboard must occupy about 52–58% of the canvas and be the single largest, clearest visual element. The left student and center input device should be smaller. The complete flow must read instantly from left to right: stuck student → copy prompt with question → complete teacher-like explanation.

LEFT:
Show a natural-looking 12–14-year-old Chinese student studying alone, frustrated after searching through several confusing answers. Use cool, dark gray-blue lighting. The student has an open workbook and looks stuck, but not dramatically sad. Show a few abstract, unreadable search-result cards around the workbook.

CENTER:
Show a clean smartphone or tablet interface receiving two distinct items: a photographed homework question and a reusable prompt card being copied into the conversation. Use a clear copy icon and send arrow. Keep all generated interface text abstract and unreadable. Make the transition arrow obvious but elegant.

RIGHT:
Create a bright, polished AI tutoring answer dashboard. It must contain exactly FIVE large, clearly separated, mostly blank content cards with generous empty label areas for typography to be added later:
1. a plain-language explanation card with simple speech-bubble icon and short abstract lines;
2. a why-it-works reasoning card with a small cause-and-effect diagram;
3. a familiar real-life analogy card with simple everyday-object illustration;
4. a step-by-step solution card with visible numbered steps 1, 2, 3 and abstract equations;
5. a short understanding-check card with a question mark and check symbol.

The five cards must look like meaningful parts of a complete tutoring answer, not decorative pictures and not a search-results list. Leave enough clean blank space at the top of every card for deterministic Chinese or English labels. A subtle teacher-like pointer or guiding hand may appear, but no teacher character should dominate the dashboard. Show the same Chinese student on the far right edge becoming relaxed and engaged, but do not let the person cover the answer cards.

TOP TYPOGRAPHY ZONE:
Reserve a quiet, dark translucent band across the upper 20–23% of the image with no faces, icons, or UI elements so exact headline and subtitle can be added later.

Style: modern premium editorial illustration, natural Chinese student, polished educational product visual, crisp UI cards, soft natural lighting, accessible contrast, warm blue-green clarity on the right, strong left-to-right transformation from confusion to clarity, professional and shareable, not childish.

Output: landscape 16:9, designed for 1600×900, important content kept within safe margins.

Avoid all readable text, Chinese characters, English words, gibberish typography, logos, watermarks, robots, cyberpunk visuals, Western students, childish cartoon style, clutter, tiny cards, illegible UI, and an answer panel containing only decorative pictures.
```

## Deterministic typography

Chinese:

- Headline: `复制 Prompt 后，AI 会给你什么？`
- Subtitle: `不是只给答案，而是像老师一样讲到你懂。`
- Call to action: `一个 Prompt，获得一整套讲解`
- Input label: `题目 + Prompt`
- Transition label: `复制并发送`
- Answer cards: `大白话解释` · `为什么` · `生活类比` · `分步解题` · `检查是否真懂`

English:

- Headline: `What do you get after using the prompt?`
- Subtitle: `Not just an answer—an explanation that teaches until it clicks.`
- Call to action: `One prompt. A complete tutoring answer.`
- Input label: `Question + Prompt`
- Transition label: `Copy & send`
- Answer cards: `Plain-language idea` · `Why it works` · `Real-life analogy` · `Step by step` · `Check your understanding`

## Output requirements

- Canvas: 1600 × 900, landscape PNG.
- Preserve the text-free generation as `hero-background.png`.
- Add exact Chinese text in `hero.png` and English text in `hero.en.png`.
- Keep the answer dashboard as the largest visual element.
- No AI-generated typography, logos, watermarks, or branded interfaces.
