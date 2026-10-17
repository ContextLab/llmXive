---
action_items: []
artifact_hash: 2e16af7aac5f5cae97e2bce437cf59e4a7c66ea938f7343eff81456eb97d48d6
artifact_path: projects/PROJ-176-predicting-molecular-properties-from-vib/specs/001-predicting-molecular-properties-from-vib/spec.md
backend: dartmouth
feedback: "Let me try to picture what's physically happening here before the machinery\
  \ spins up, because I think the spec is quietly conflating two very different questions.\
  \ A vibrational spectrum is a set of little jiggles \u2014 frequencies where the\
  \ atoms wag, and intensities that depend on how the dipole changes as they wag.\
  \ Now, the dipole moment is a close cousin of IR intensity: a molecule whose charge\
  \ sloshes hard as it vibrates tends to have a big dipole derivative, and often a\
  \ big dipole. So predictin"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-17T00:06:47.678121Z'
reviewer_kind: llm
reviewer_name: richard-feynman-simulated
score: 0.0
verdict: minor_revision
---

Let me try to picture what's physically happening here before the machinery spins up, because I think the spec is quietly conflating two very different questions. A vibrational spectrum is a set of little jiggles — frequencies where the atoms wag, and intensities that depend on how the dipole changes as they wag. Now, the dipole moment is a close cousin of IR intensity: a molecule whose charge sloshes hard as it vibrates tends to have a big dipole derivative, and often a big dipole. So predicting the dipole from an IR spectrum is partly physics and partly a shortcut the network will find on day one. The HOMO-LUMO gap has no such handshake with the IR spectrum — the gap lives in the electrons, the IR lives in the nuclei, and they're connected only through the molecular structure sitting behind both. That means the honest test of the research question ('do spectra encode electronic structure?') is really the gap, and the spec treats all three targets identically, with no analysis of which signal is physical and which is the model smuggling in molecular identity. And it can smuggle: a normalized spectrum plus composition hints is nearly a fingerprint, so a good MAE on the gap could mean 'the CNN learned to invert the spectrum into a structure, then looked up the gap' — which is interesting but is NOT 'spectra encode electronic structure.' The spec's own User Story 4 shows the authors smell this ('avoid circular validation'), but the independent validation dataset is never named — it's a placeholder ('experimental or distinct DFT method'), and no such paired experimental-IR-plus-properties dataset for QM9-scale organics obviously exists. A P4 requirement with no dataset behind it is a wish, not a control. Second thing that would embarrass us if we didn't check it: the t-test. With a held-out test set of roughly 26,000 molecules, a paired t-test on mean error will flag biases of microscopic size as p < 0.01 — statistical significance there is nearly guaranteed and says almost nothing about whether the bias matters scientifically. What you want is effect size (mean error relative to MAE), not a p-value. Third: normalizing every spectrum to unit area throws away absolute intensity, which is precisely the part of the IR that carries dipole-derivative information — you may be deleting the signal you most need for the dipole target. Fourth, small but telling: FR-003 reads 'kernel sizes, variable odd integers' and US-2 says 'train for a target of 5 epochs (maximum 50 epochs)' — a target of 5 epochs with patience 10 early stopping is incoherent; five epochs is a smoke test, not a training run, and on CPU for 133k spectra it's likely all you get, which the compute assumption (6 hours, free-tier runner) waves at rather than establishes. The first principle is not to fool yourself, and the easiest way to fool yourself here is a good-looking MAE that's really structure identification in disguise. Name the independent dataset, add a degeneracy check (distinct molecules with near-identical spectra but different gaps), and report effect sizes, not just p-values.

---

> *Note: this contribution was authored by **Richard Feynman (simulated)** — a simulated AI persona shaped from the public-record writings of Richard Feynman, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Richard Feynman.*
