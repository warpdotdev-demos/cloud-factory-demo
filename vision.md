# Vision

This example app is a simple, useful text-based image editor built around the best available state-of-the-art image editing model.

The product goal is to help users get from an image they have to an image they want in as few steps as possible. Instead of exposing a complex professional editing surface with layers, masks, blend modes, and tool palettes, the app should let users describe the outcome they want in natural language, preview the result, refine it, and keep moving.

## Product direction

The app should prioritize:

- **Low-friction editing**: A user should be able to upload or select an image, describe a desired change, and receive a useful edited result quickly.
- **Iterative refinement**: Editing should feel conversational. Users should be able to make follow-up requests that build on the current image without restarting from scratch.
- **Model quality over manual controls**: The app should rely on the strongest practical image generation and editing model available, while keeping the interface focused on intent rather than technical model details.
- **Clear user confidence**: Users should understand what image is being edited, what prompt or instruction is being applied, and what result was produced.
- **Useful defaults**: Common tasks such as style transfer, cleanup, background changes, resizing, and export should work with minimal setup.
- **Demo-friendly implementation**: The codebase should stay small enough to be understandable in a demo, while still being realistic enough for agents to triage, spec, implement, review, and validate changes.

## Cloud factory purpose

This repository is also an example app for demonstrating a cloud software factory. The image editor should create realistic product work for automated agents to handle across the software development lifecycle:

- Triage new issues against the app's product direction.
- Route simple, well-scoped issues directly to implementation.
- Route larger or ambiguous features into product and technical specs.
- Produce pull requests that humans can review instead of merging automatically.
- Keep the product small enough that the factory flow is easy to explain, observe, and trust.

The ideal issue for this app is not just technically possible; it should make the text-based image editing experience simpler, faster, more reliable, or easier to understand.

## Non-goals

This app should not try to become a full professional image editor. It should avoid deep manual editing workflows unless they directly support the goal of helping users reach desired images through concise text-driven interactions.

This app should also avoid infrastructure complexity that distracts from the factory demo. Durable storage, authentication, billing, collaboration, and advanced asset management can be introduced only when they make the demo flow or product story substantially better.
