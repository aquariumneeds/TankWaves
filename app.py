{% extends "base.html" %}
{% block title %}Log in — TankWaves{% endblock %}
{% block content %}
<section class="container auth-wrap">
  <form class="form-card" method="post">
    <span class="eyebrow">WELCOME BACK</span>
    <h1>Log in</h1>
    <label>Email or account name<input name="email" required autocomplete="username"></label>
    <label>Password<input type="password" name="password" required autocomplete="current-password"></label>
    <button class="button" type="submit">Log in</button>
    <p>New to TankWaves? <a href="{{ url_for('register') }}">Create an account</a>.</p>
  </form>
</section>
{% endblock %}
