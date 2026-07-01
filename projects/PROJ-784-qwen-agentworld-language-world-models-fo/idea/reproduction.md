# Reproduce & validate: Qwen-AgentWorld: Language World Models for General Agents

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-784-qwen-agentworld-language-world-models-fo/external/express/   (clone of https://github.com/expressjs/express)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Qwen-AgentWorld: Language World Models for General Agents

**Abstract:** A world model predicts environment dynamics based on current observations and actions, serving as a core cognitive mechanism for reasoning and planning. In this work, we investigate how world modeling based on language models can further push the boundaries of general agents. (i) We first focus on building foundation models for agentic environment simulation. We introduce Qwen-AgentWorld-35B-A3B and Qwen-AgentWorld-397B-A17B, the first language world models capable of simulating agentic environments covering 7 domains via long chain-of-thought reasoning. Leveraging more than 10M environment interaction trajectories of 7 domains in real-world environments, we develop Qwen-AgentWorld through a three-stage training pipeline: CPT injects general-purpose world modeling capabilities from the state transition dynamics and augmented professional corpora, SFT activates next-state-prediction reasoning, and RL sharpens simulation fidelity through a tailored framework with hybrid rubric-and-rule rewards. To evaluate language world models, we present AgentWorldBench, a comprehensive benchmark constructed from real-world interactions of 5 frontier models on 9 established benchmarks. Empirical results demonstrate that Qwen-AgentWorld significantly outperforms existing frontier models. (ii) Beyond foundation models, we further investigate two complementary paradigms through which world modeling enhances general agents. First, as a decoupled environment simulator, Qwen-AgentWorld supports scalable and controllable simulation of thousands of real-world environments for agentic RL, yielding gains that surpass real-environment training alone. Second, as a unified agent foundation model, world-model training acts as a highly effective warm-up that improves downstream performance across 7 agentic benchmarks. Code: https://github.com/QwenLM/Qwen-AgentWorld

## Shipped code — file tree (`projects/PROJ-784-qwen-agentworld-language-world-models-fo/external/express/`)

```
.editorconfig
.eslintignore
.eslintrc.yml
.github/dependabot.yml
.github/workflows/ci.yml
.github/workflows/codeql.yml
.github/workflows/legacy.yml
.github/workflows/scorecard.yml
.gitignore
.npmrc
History.md
LICENSE
Readme.md
examples/README.md
examples/auth/index.js
examples/auth/views/foot.ejs
examples/auth/views/head.ejs
examples/auth/views/login.ejs
examples/content-negotiation/db.js
examples/content-negotiation/index.js
examples/content-negotiation/users.js
examples/cookie-sessions/index.js
examples/cookies/index.js
examples/downloads/files/CCTV大赛上海分赛区.txt
examples/downloads/files/amazing.txt
examples/downloads/files/notes/groceries.txt
examples/downloads/index.js
examples/ejs/index.js
examples/ejs/public/stylesheets/style.css
examples/ejs/views/footer.html
examples/ejs/views/header.html
examples/ejs/views/users.html
examples/error/index.js
examples/error-pages/index.js
examples/error-pages/views/404.ejs
examples/error-pages/views/500.ejs
examples/error-pages/views/error_header.ejs
examples/error-pages/views/footer.ejs
examples/error-pages/views/index.ejs
examples/hello-world/index.js
examples/markdown/index.js
examples/markdown/views/index.md
examples/multi-router/controllers/api_v1.js
examples/multi-router/controllers/api_v2.js
examples/multi-router/index.js
examples/mvc/controllers/main/index.js
examples/mvc/controllers/pet/index.js
examples/mvc/controllers/pet/views/edit.ejs
examples/mvc/controllers/pet/views/show.ejs
examples/mvc/controllers/user/index.js
examples/mvc/controllers/user/views/edit.hbs
examples/mvc/controllers/user/views/list.hbs
examples/mvc/controllers/user/views/show.hbs
examples/mvc/controllers/user-pet/index.js
examples/mvc/db.js
examples/mvc/index.js
examples/mvc/lib/boot.js
examples/mvc/public/style.css
examples/mvc/views/404.ejs
examples/mvc/views/5xx.ejs
examples/online/index.js
examples/params/index.js
examples/resource/index.js
examples/route-map/index.js
examples/route-middleware/index.js
examples/route-separation/index.js
examples/route-separation/post.js
examples/route-separation/public/style.css
examples/route-separation/site.js
examples/route-separation/user.js
examples/route-separation/views/footer.ejs
examples/route-separation/views/header.ejs
examples/route-separation/views/index.ejs
examples/route-separation/views/posts/index.ejs
examples/route-separation/views/users/edit.ejs
examples/route-separation/views/users/index.ejs
examples/route-separation/views/users/view.ejs
examples/search/index.js
examples/search/public/client.js
examples/search/public/index.html
examples/session/index.js
examples/session/redis.js
examples/static-files/index.js
examples/static-files/public/css/style.css
examples/static-files/public/hello.txt
examples/static-files/public/js/app.js
examples/vhost/index.js
examples/view-constructor/github-view.js
examples/view-constructor/index.js
examples/view-locals/index.js
examples/view-locals/user.js
examples/view-locals/views/index.ejs
examples/web-service/index.js
index.js
lib/application.js
lib/express.js
lib/request.js
lib/response.js
lib/utils.js
lib/view.js
package.json
test/Route.js
test/Router.js
test/acceptance/auth.js
test/acceptance/content-negotiation.js
test/acceptance/cookie-sessions.js
test/acceptance/cookies.js
test/acceptance/downloads.js
test/acceptance/ejs.js
test/acceptance/error-pages.js
test/acceptance/error.js
test/acceptance/hello-world.js
test/acceptance/markdown.js
test/acceptance/multi-router.js
test/acceptance/mvc.js
test/acceptance/params.js
test/acceptance/resource.js
test/acceptance/route-map.js
test/acceptance/route-separation.js
test/acceptance/vhost.js
test/acceptance/web-service.js
test/app.all.js
test/app.engine.js
test/app.head.js
test/app.js
test/app.listen.js
test/app.locals.js
test/app.options.js
test/app.param.js
test/app.render.js
test/app.request.js
test/app.response.js
test/app.route.js
test/app.router.js
test/app.routes.error.js
test/app.use.js
test/config.js
test/exports.js
test/express.json.js
test/express.raw.js
test/express.static.js
test/express.text.js
test/express.urlencoded.js
test/fixtures/% of dogs.txt
test/fixtures/.name
test/fixtures/blog/index.html
test/fixtures/blog/post/index.tmpl
test/fixtures/broken.send
test/fixtures/default_layout/name.tmpl
test/fixtures/default_layout/user.tmpl
test/fixtures/email.tmpl
test/fixtures/empty.txt
test/fixtures/local_layout/user.tmpl
test/fixtures/name.tmpl
test/fixtures/name.txt
test/fixtures/nums.txt
test/fixtures/pets/names.txt
test/fixtures/snow ☃/.gitkeep
test/fixtures/todo.html
test/fixtures/todo.txt
test/fixtures/user.html
test/fixtures/user.tmpl
test/fixtures/users/index.html
test/fixtures/users/tobi.txt
test/middleware.basic.js
test/regression.js
test/req.accepts.js
test/req.acceptsCharsets.js
test/req.acceptsEncodings.js
test/req.acceptsLanguages.js
test/req.baseUrl.js
test/req.fresh.js
test/req.get.js
test/req.host.js
test/req.hostname.js
test/req.ip.js
test/req.ips.js
test/req.is.js
test/req.path.js
test/req.protocol.js
test/req.query.js
test/req.range.js
test/req.route.js
test/req.secure.js
test/req.signedCookies.js
test/req.stale.js
test/req.subdomains.js
test/req.xhr.js
test/res.append.js
test/res.attachment.js
test/res.clearCookie.js
test/res.cookie.js
test/res.download.js
test/res.format.js
test/res.get.js
test/res.json.js
test/res.jsonp.js
test/res.links.js
test/res.locals.js
test/res.location.js
… (truncated)
```

## Detected entry points

- (no .py entry scripts auto-detected; see README usage)

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `express` — not re-implementing it.
