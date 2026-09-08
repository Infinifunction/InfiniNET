#-------------------------------------------#
# Creates the dynamic authentication HTML interface used by the application.
# The function builds the complete page as a single HTML string, including the
# optional error message, styling, authentication form, and system branding.
# Configuration values required to construct the form URL are imported locally
# to avoid a circular module dependency during application startup.
#-------------------------------------------#
def create_html(error_message=""):
    from config import MY_IP, PROXY_PORT
    
    html_error = ""
    if error_message:
        html_error = f"""
        <div style="background: rgba(139, 29, 29, 0.2); border: 1px solid var(--accent); padding: 12px; border-radius: 4px; font-size: 12px; color: #ff6b6b; margin-bottom: 20px; text-align: left; font-family: 'Inter', sans-serif; letter-spacing: 0.05em; animation: rise 0.5s ease;">
            <strong>⚠️ SYSTEM ERROR:</strong> {error_message}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>InfiniNET — Login</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

  :root{{
    --ink-black: #06070a;
    --void: #0a0c10;
    --steel: #b9bfc9;
    --steel-bright: #e7eaef;
    --steel-dim: #5b616c;
    --line: rgba(185,191,201,0.18);
    --line-bright: rgba(185,191,201,0.4);
    --accent: #8b1d1d;
    --accent-bright: #c23a3a;
    --glass: rgba(12,14,18,0.55);
  }}

  *{{ margin:0; padding:0; box-sizing:border-box; }}

  html,body{{
    height:100%;
    background: var(--ink-black);
    font-family: 'Inter', sans-serif;
    color: var(--steel-bright);
    overflow-x:hidden;
  }}

  body{{
    min-height:100vh;
    position:relative;
    display:flex;
    align-items:center;
    justify-content:center;
    padding: 32px 18px;
  }}

  .bg{{
    position:fixed;
    inset:0;
    background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFklEQVQYlWNgYGD4DwUMIEwMZGBgAAAAMQEXBcHZ3gAAAABJRU5ErkJggg=='), radial-gradient(circle at center, #141923 0%, var(--ink-black) 100%);
    background-size: 6px 6px, auto;
    filter: saturate(0.85) contrast(1.05);
    z-index:0;
  }}
  .bg::after{{
    content:'';
    position:absolute;
    inset:0;
    background:
      radial-gradient(ellipse 120% 70% at 50% 8%, rgba(6,7,10,0.15) 0%, rgba(6,7,10,0.55) 38%, rgba(6,7,10,0.93) 72%, var(--ink-black) 100%),
      linear-gradient(180deg, rgba(6,7,10,0.35) 0%, rgba(6,7,10,0.2) 30%, rgba(6,7,10,0.75) 75%, var(--ink-black) 100%);
  }}

  .grain{{
    position:fixed; inset:0; z-index:1; pointer-events:none;
    opacity:0.04; mix-blend-mode:overlay;
    background-image:
      repeating-linear-gradient(0deg, #fff 0px, transparent 1px, transparent 2px, #fff 3px);
  }}

  .vignette{{
    position:fixed; inset:0; z-index:1; pointer-events:none;
    box-shadow: inset 0 0 18vw 4vw rgba(0,0,0,0.85);
  }}

  .frame-mark{{
    position:fixed;
    width:22px; height:22px;
    border: 1px solid var(--line-bright);
    z-index:5;
    opacity:0.7;
  }}
  .frame-mark.tl{{ top:18px; left:18px; border-right:none; border-bottom:none; }}
  .frame-mark.tr{{ top:18px; right:18px; border-left:none; border-bottom:none; }}
  .frame-mark.bl{{ bottom:18px; left:18px; border-right:none; border-top:none; }}
  .frame-mark.br{{ bottom:18px; right:18px; border-left:none; border-top:none; }}

  .case-id{{
    position:fixed;
    top:24px; left:50%; transform:translateX(-50%);
    font-family:'Oswald',sans-serif;
    font-size:10px;
    letter-spacing:0.32em;
    color: var(--steel-dim);
    text-transform:uppercase;
    z-index:5;
    text-align:center;
  }}

  .stage{{
    position:relative;
    z-index:3;
    width:100%;
    max-width:400px;
    display:flex;
    flex-direction:column;
    align-items:center;
  }}

  .seal-wrap{{
    position:relative;
    width:148px;
    height:148px;
    margin-bottom:6px;
    animation: rise 1s cubic-bezier(.16,1,.3,1) both;
  }}
  .seal-wrap img{{
    width:100%; height:100%;
    object-fit:contain;
    filter: drop-shadow(0 0 26px rgba(189,29,29,0.4)) drop-shadow(0 8px 18px rgba(0,0,0,0.7));
  }}
  .seal-ring{{
    position:absolute; inset:-10px;
    border-radius:50%;
    border: 1px solid var(--line);
    animation: spin 70s linear infinite;
  }}
  .seal-ring::before{{
    content:'';
    position:absolute;
    top:-2px; left:50%;
    width:4px; height:4px;
    background:var(--steel-dim);
    border-radius:50%;
    transform:translateX(-50%);
  }}

  .org-name{{
    font-family:'Oswald', sans-serif;
    font-weight:600;
    font-size:30px;
    letter-spacing:0.42em;
    color: var(--steel-bright);
    text-align:center;
    margin: 10px 0 2px 2px;
    text-shadow: 0 2px 18px rgba(0,0,0,0.7);
    animation: rise 1s cubic-bezier(.16,1,.3,1) 0.08s both;
  }}

  .org-sub{{
    font-family:'Inter', sans-serif;
    font-weight:400;
    font-size:11px;
    letter-spacing:0.28em;
    color: var(--steel-dim);
    text-transform:uppercase;
    margin-bottom:30px;
    text-align:center;
    animation: rise 1s cubic-bezier(.16,1,.3,1) 0.14s both;
  }}

  .divider{{
    width:100%;
    display:flex; align-items:center; gap:10px;
    margin-bottom:26px;
    animation: rise 1s cubic-bezier(.16,1,.3,1) 0.18s both;
  }}
  .divider::before,.divider::after{{
    content:''; flex:1; height:1px;
    background:linear-gradient(90deg, transparent, var(--line-bright), transparent);
  }}
  .divider span{{
    font-family:'Oswald',sans-serif;
    font-size:9px;
    letter-spacing:0.3em;
    color:var(--steel-dim);
    white-space:nowrap;
    text-transform:uppercase;
  }}

  .card{{
    width:100%;
    background: var(--glass);
    backdrop-filter: blur(18px) saturate(120%);
    -webkit-backdrop-filter: blur(18px) saturate(120%);
    border: 1px solid var(--line);
    border-radius: 4px;
    padding: 30px 26px 28px;
    position:relative;
    animation: rise 1s cubic-bezier(.16,1,.3,1) 0.22s both;
    box-shadow:
      0 30px 60px -20px rgba(0,0,0,0.7),
      inset 0 1px 0 rgba(255,255,255,0.04);
  }}
  .card::before, .card::after{{
    content:'';
    position:absolute;
    width:14px; height:14px;
    border-color: var(--steel-dim);
    border-style:solid;
    opacity:0.55;
  }}
  .card::before{{ top:-1px; left:-1px; border-width:1px 0 0 1px; }}
  .card::after{{ bottom:-1px; right:-1px; border-width:0 1px 1px 0; }}

  .field{{
    margin-bottom:18px;
    position:relative;
  }}
  .field label{{
    display:block;
    font-family:'Oswald',sans-serif;
    font-size:10px;
    letter-spacing:0.22em;
    text-transform:uppercase;
    color: var(--steel-dim);
    margin-bottom:8px;
  }}
  .field input{{
    width:100%;
    background: rgba(255,255,255,0.025);
    border: 1px solid var(--line);
    border-radius: 2px;
    padding: 13px 14px;
    font-family:'Inter',sans-serif;
    font-size:14px;
    color: var(--steel-bright);
    letter-spacing:0.02em;
    transition: border-color .25s ease, background .25s ease, box-shadow .25s ease;
  }}
  .field input::placeholder{{ color: rgba(185,191,201,0.28); }}
  .field input:focus{{
    outline:none;
    border-color: var(--steel-bright);
    background: rgba(255,255,255,0.045);
    box-shadow: 0 0 0 3px rgba(185,191,201,0.08);
  }}

  .row-aux{{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin: -4px 0 24px;
    font-size:12px;
  }}
  .remember{{
    display:flex; align-items:center; gap:8px;
    color: var(--steel-dim);
    cursor:pointer;
    user-select:none;
  }}
  .remember input{{
    appearance:none;
    width:14px; height:14px;
    border:1px solid var(--line-bright);
    background:rgba(255,255,255,0.02);
    border-radius:2px;
    cursor:pointer;
    position:relative;
    transition: all .2s ease;
  }}
  .remember input:checked{{
    background: var(--steel-bright);
    border-color: var(--steel-bright);
  }}
  .remember input:checked::after{{
    content:'';
    position:absolute;
    left:4px; top:1px;
    width:4px; height:8px;
    border:solid var(--ink-black);
    border-width:0 2px 2px 0;
    transform:rotate(45deg);
  }}
  .forgot{{
    color: var(--steel-dim);
    text-decoration:none;
    border-bottom:1px solid transparent;
    transition: color .2s ease, border-color .2s ease;
  }}
  .forgot:hover{{ color: var(--steel-bright); border-color: var(--line-bright); }}

  .btn-primary{{
    width:100%;
    padding:14px;
    background: var(--steel-bright);
    color: var(--ink-black);
    border:none;
    border-radius:2px;
    font-family:'Oswald',sans-serif;
    font-size:13px;
    font-weight:600;
    letter-spacing:0.2em;
    text-transform:uppercase;
    cursor:pointer;
    position:relative;
    overflow:hidden;
    transition: transform .15s ease, box-shadow .25s ease;
  }}
  .btn-primary:hover{{
    box-shadow: 0 0 30px rgba(231,234,239,0.25);
  }}
  .btn-primary:active{{ transform: scale(0.985); }}

  .meta-line{{
    margin-top:22px;
    text-align:center;
    font-size:11.5px;
    color: var(--steel-dim);
    letter-spacing:0.02em;
  }}
  .meta-line a{{
    color: var(--steel-bright);
    text-decoration:none;
    border-bottom:1px solid var(--line-bright);
    padding-bottom:1px;
  }}

  .footer-id{{
    margin-top:28px;
    font-family:'Oswald',sans-serif;
    font-size:9.5px;
    letter-spacing:0.3em;
    color: var(--steel-dim);
    opacity:0.55;
    text-align:center;
    animation: rise 1s cubic-bezier(.16,1,.3,1) 0.3s both;
  }}

  @keyframes rise{{
    from{{ opacity:0; transform: translateY(14px); }}
    to{{ opacity:1; transform: translateY(0); }}
  }}
  @keyframes spin{{
    from{{ transform: rotate(0deg); }}
    to{{ transform: rotate(360deg); }}
  }}
</style>
</head>
<body>

  <div class="bg"></div>
  <div class="grain"></div>
  <div class="vignette"></div>

  <div class="frame-mark tl"></div>
  <div class="frame-mark tr"></div>
  <div class="frame-mark bl"></div>
  <div class="frame-mark br"></div>
  <div class="case-id">SYSTEM ACCESS — RESTRICTED AREA</div>

  <main class="stage">
    <div class="seal-wrap">
      <div class="seal-ring"></div>
      <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAMAAABwKC9UAAAAAXNSR0IArs4c6QAAAAnQTFRFAAAA////N0IAd0QA6gCcAAAA3vU68gAAAAF0Uk5TAEDm2GYAAAABYktHRACIBR1IAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH6AYMExQuKyzM3wAAAmVJREFUaN7tmV13qyAMhR0EBOv//3mvdgNisbY6p7vO7Fp7X7gJIcmHIbAslmVZlmVZlmVZltXp0fV9G86gXb3w3f7zB/QHeKPr29O07/vXgC263p0m7u+fA97o+nbXfX39DPBF18vT6OPwGvBH15fTxuX6NuArXffD4fJyF/AnXffDff98FvAndWfe+7gX8C9dZ+bZ6V7An9SdeXPcC/iXrjOz27+GfOm6M2euWwP50vW3uTIbtgbyfdfYmS2zAn0wK6FpViCDWQmhWfkhkBl6VwMypA8XAnX68Aao68Pr6K6ZAbmYmS0zA3K1/mS2gT66a98HwN6gD836+gDWDfog06wZ9OEFZgV9BIFZQR9BYFbQhxeYFfThBWYFfXiBWUEfXmBW0Gf6ZtYI+kzfMxsFfXgBfXgBffS7bwb66AekU/LpIwjMCvoIArOCPoLArKAPLzAr6MMLzAr68AKzgj68wKygDy8wK+jDC8wK+kzfPxsFfaZveNcsgPzM6pMh/898ZpWzSdA3m2YF+rBvVs6mGZCPvpkZ6NuOmWfTDtCHb6NfNfXpBvS5MvsasA/0fSvsA33XCluBvmsf/wH6rtV9vjHw/Nn/C+gXjW6ZFehzvffNCvR5Pft6vYt+X937vD9FH8gXW76YFeiDWdfMvI8gMCvoIwjMCvoIArOCPvKAvKAPLzAr6MMLzAr68AKzgj68wKygz/TNrBH0mb5nNgr68IIm6MML8OEDfR+fofA+WwJ9s6/ZpEAfNvs7vX+E/rOfGfSRvsw6AfoW6v0X6CMMzAr6mDPW/+Xg/gP6327b9wX6Z/I7V6B/Pvd/A/0v5L/7C/Rfnft/gYv+6v0B6fV8ZpI6jNAAAAAElFTkSuQmCC" alt="InfiniNET Emblem">
    </div>

    <h1 class="org-name">InfiniNET</h1>
    <p class="org-sub">Authorized Personnel Login</p>

    <div class="divider"><span>Authentication</span></div>

    {html_error}

    <form class="card" action="http://{MY_IP}:{PROXY_PORT}/" method="GET" autocomplete="off">
      <div class="field">
        <label for="user">Username / Personnel ID</label>
        <input type="text" id="user" name="user" placeholder="e.g. M-04217" required>
      </div>
      <div class="field">
        <label for="pass">Parola</label>
        <input type="password" id="pass" name="pass" placeholder="••••••••••" required>
      </div>

      <div class="row-aux">
        <label class="remember">
          <input type="checkbox">
          Keep me signed in
        </label>
        <a href="#" class="forgot">Forgot password</a>
      </div>

      <button type="submit" class="btn-primary">Sign In</button>

      <p class="meta-line">For access requests, <a href="#">contact the authorized department</a></p>
    </form>

    <p class="footer-id">PROTOCOL 7 · ALL ACCESS ATTEMPTS ARE LOGGED</p>
  </main>

</body>
</html>"""
