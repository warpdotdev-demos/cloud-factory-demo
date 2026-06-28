# Roadmap

This roadmap expands the product vision into high-level areas of work for the example text-based image editor. It is intentionally abstract: the goal is to give triage and spec agents enough product direction to decide whether an issue belongs in the app, whether it is simple enough to implement directly, or whether it should first become a spec.

## 1. Core text-based editing loop

Build the simplest reliable path from source image to edited image.

Possible work includes:

- Uploading or selecting an image to edit.
- Entering a natural-language edit instruction.
- Sending the image and instruction to the current best image editing model.
- Displaying the edited result next to the original.
- Supporting follow-up edits that continue from the latest result.
- Making loading, error, retry, and empty states clear.

This area is central to the vision. Clear, bounded improvements to the core loop are usually good candidates for implementation. Broad changes to editing state, model interaction, or multi-step refinement may need specs.

## 2. Prompt assistance and useful defaults

Help users express the image they want without needing to know prompt engineering.

Possible work includes:

- Suggested edit prompts for common tasks.
- Prompt templates for style transfer, cleanup, background replacement, object removal, and enhancement.
- Lightweight prompt rewriting or clarification before model execution.
- Example prompts that demonstrate what the app can do.
- Guardrails that keep prompts focused on image editing outcomes.

This area should make the app easier to use in fewer steps. Features that add complexity without reducing user effort should be treated cautiously.

## 3. Result comparison and iteration

Make it easy for users to understand and refine model outputs.

Possible work includes:

- Original/result comparison views.
- Edit history for the current session.
- Reverting to earlier results.
- Re-running an edit with the same instruction.
- Showing the prompt or instruction used for each result.
- Letting users branch from a previous result when that keeps the flow understandable.

Simple UI improvements in this area may be ready to implement. Larger changes to history models or branching behavior should usually be ready to spec.

## 4. Export and sharing

Let users take useful results out of the app.

Possible work includes:

- Downloading edited images.
- Choosing common export sizes or quality presets.
- Preserving useful filenames and metadata when practical.
- Copying generated images to the clipboard.
- Sharing a result in a demo-friendly way without requiring accounts.

Export features should stay lightweight unless a real demo or product need justifies more complexity.

## 5. Model abstraction and provider evolution

Keep the app oriented around the best available image editing model without coupling the product experience too tightly to one provider.

Possible work includes:

- A small model/provider abstraction for image editing requests.
- Clear handling of provider errors, rate limits, and unsupported inputs.
- Configuration that makes it easy to swap the backing model for demos.
- Capturing enough request/response metadata to debug failures without exposing secrets.

Changes here can be technically important but may be risky. Anything that touches provider selection, secrets, request formats, or model-specific behavior should usually receive careful implementation or a spec first.

## 6. Demo-quality reliability and observability

Make the app dependable enough for live demos and agent-driven development.

Possible work includes:

- Fast local setup instructions.
- Clear environment variable documentation.
- Basic smoke tests for the editing flow.
- Error messages that help a user recover.
- Minimal logging for debugging model calls without leaking prompts, images, or secrets unnecessarily.
- Fixtures or mocked model responses for deterministic testing.

This area supports both the product and the cloud factory demo. Small reliability fixes are usually ready to implement; larger testing or observability systems may need specs.

## 7. Cloud factory demonstration features

Use the app as a realistic target for demonstrating automated SDLC workflows.

Possible work includes:

- Issues that are intentionally small enough for direct implementation.
- Issues that are intentionally broad enough to require PRODUCT.md and TECH.md specs.
- Example roadmap and vision documents that guide triage decisions.
- Spec artifacts under `specs/<issue-slug>/PRODUCT.md` and `specs/<issue-slug>/TECH.md`.
- Clear pull request descriptions and validation notes from implementation agents.
- Review and verification patterns that show humans staying in the loop.

This area should improve the demo software factory itself, but changes should still relate to building or operating the example image editor.

## Triage guidance

Issues should generally be classified as:

- **Ready to implement** when the desired behavior is clear, cohesive, low-risk, and likely small enough for a coding agent to complete directly.
- **Ready to spec** when the issue fits this roadmap and vision but involves meaningful product choices, technical architecture, provider abstractions, state management, or more than a few hundred lines of likely implementation work.
- **Needs info** when the expected behavior, user problem, inputs, outputs, or acceptance criteria are unclear.
- **Wait to implement** when the request does not support a simple text-based image editing experience or distracts from the cloud factory demo.
