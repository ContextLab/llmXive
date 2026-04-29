// llmXive OAuth proxy. Exchanges a GitHub authorization `code` for an access
// token, keeping `client_secret` server-side. Designed for Cloudflare Workers
// free tier (~200 LOC).
//
// Deploy:
//   wrangler secret put GITHUB_CLIENT_SECRET
//   wrangler deploy
//
// Endpoints:
//   POST /authenticate   { code, state } → { access_token, scope, token_type }
//   GET  /healthz        → "ok"
//
// Security:
//   * client_secret is read from a Worker secret, never the source.
//   * CORS is restricted to `ALLOWED_ORIGIN` (the public site).
//   * The browser is responsible for verifying its own `state` (we trust it).

interface Env {
  GITHUB_CLIENT_ID: string;
  GITHUB_CLIENT_SECRET: string;
  ALLOWED_ORIGIN: string;
}

function corsHeaders(env: Env): Record<string, string> {
  return {
    "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

async function exchangeCode(env: Env, code: string): Promise<Response> {
  const r = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code,
    }),
  });
  if (!r.ok) {
    return new Response(
      JSON.stringify({ error: `github_${r.status}`, detail: await r.text() }),
      { status: 502, headers: { "Content-Type": "application/json", ...corsHeaders(env) } },
    );
  }
  const data = await r.json();
  if (!data.access_token) {
    return new Response(
      JSON.stringify({ error: "no_token", detail: data }),
      { status: 502, headers: { "Content-Type": "application/json", ...corsHeaders(env) } },
    );
  }
  return new Response(
    JSON.stringify({
      access_token: data.access_token,
      scope: data.scope,
      token_type: data.token_type,
    }),
    { status: 200, headers: { "Content-Type": "application/json", ...corsHeaders(env) } },
  );
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(env) });
    }

    if (url.pathname === "/healthz") {
      return new Response("ok", {
        status: 200,
        headers: { "Content-Type": "text/plain", ...corsHeaders(env) },
      });
    }

    if (url.pathname === "/authenticate" && request.method === "POST") {
      let body: unknown;
      try { body = await request.json(); }
      catch { return new Response(JSON.stringify({ error: "bad_json" }), {
        status: 400, headers: { "Content-Type": "application/json", ...corsHeaders(env) },
      }); }
      const code = (body as { code?: string }).code;
      if (!code || typeof code !== "string") {
        return new Response(JSON.stringify({ error: "missing_code" }), {
          status: 400, headers: { "Content-Type": "application/json", ...corsHeaders(env) },
        });
      }
      return exchangeCode(env, code);
    }

    return new Response("Not found", {
      status: 404,
      headers: { "Content-Type": "text/plain", ...corsHeaders(env) },
    });
  },
};
