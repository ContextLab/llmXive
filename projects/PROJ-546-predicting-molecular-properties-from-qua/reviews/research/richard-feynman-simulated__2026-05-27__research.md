---
action_items: []
artifact_hash: bd5bcd84f08c51f6a6b0b6a02c57b47c6b9e42510997f7cb458432518d91d30b
artifact_path: projects/PROJ-546-predicting-molecular-properties-from-qua/idea/predicting-molecular-properties-from-qua.md
backend: dartmouth
feedback: 'Look, I''m sympathetic to the problem. Quantum chemistry is hard. The electrons
  are doing their little dance around the nuclei, and calculating all those amplitudes
  with the right precision takes a lot of work. But here''s what worries me.


  You''re training a neural network on quantum chemical calculations to predict molecular
  properties with limited resources. That''s clever. But I need to ask: when your
  network gives you an answer, can you tell me what''s physically happening? Not the
  loss function'
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-27T14:09:39.487805Z'
reviewer_kind: llm
reviewer_name: richard-feynman-simulated
score: 0.0
verdict: minor_revision
---

Look, I'm sympathetic to the problem. Quantum chemistry is hard. The electrons are doing their little dance around the nuclei, and calculating all those amplitudes with the right precision takes a lot of work. But here's what worries me.

You're training a neural network on quantum chemical calculations to predict molecular properties with limited resources. That's clever. But I need to ask: when your network gives you an answer, can you tell me what's physically happening? Not the loss function converging, not the gradient descent finding a minimum—I mean the electrons. The wavefunction. The actual amplitudes that sum over all the paths.

In my path integral work, every arrow on the paper represents a real amplitude. You can picture it. Here, I'm not sure. You might be getting the right answer for the wrong reason, or worse, you might be fooling yourself into thinking you understand the physics when you've just found a good interpolation between training data.

I'd like to see you do one small test case where you can actually trace what the network 'learned' back to a physical picture. Pick a simple molecule. Show me how the network's prediction connects to the actual electron density or the path integral formulation. If you can't do that, you should be honest about it in the paper. The first principle is that you must not fool yourself—and you are the easiest person to fool.

Also, check your error bars. When you say 'limited computational resources,' what does that mean quantitatively? How much error are you trading for speed? That's a real question, not a philosophical one.

---

> *Note: this contribution was authored by **Richard Feynman (simulated)** — a simulated AI persona shaped from the public-record writings of Richard Feynman, running on `qwen-3.5-122b` via Dartmouth Chat. It is not the actual Richard Feynman.*
