{% extends "base.html" %}
{% block title %}Aquarium Sellers — TankWaves{% endblock %}
{% block content %}
<section class="container results-head">
  <span class="eyebrow">SELLER DIRECTORY</span>
  <h1>Stores, breeders, and hobbyists</h1>
  <p>Browse independent aquarium sellers and visit their TankWaves storefronts.</p>
</section>
<section class="container search-panel directory-search">
  <form method="get" action="{{ url_for('stores_directory') }}">
    <input name="q" value="{{ q or '' }}" placeholder="Search by store, city, state, or specialty">
    <button class="button" type="submit">Search sellers</button>
  </form>
</section>
<section class="container section">
  <div class="store-grid directory-grid">
    {% for store in stores %}
      <a class="store-card directory-card" href="{{ url_for('storefront', slug=store.slug) }}">
        {% if store.logo_url %}<img src="{{ store.logo_url }}" alt="{{ store.name }} logo">{% else %}<div class="initial">{{ store.name[0] }}</div>{% endif %}
        <div>
          <h3>{{ store.name }}</h3>
          <p>{{ store.owner.city }}, {{ store.owner.state }}</p>
          <p>{{ (store.description or "Aquarium seller on TankWaves")[:110] }}</p>
          <span class="rating">★ {{ "%.1f"|format(store.rating_average) }} ({{ store.reviews|length }})</span>
          {% if store.verified %}<span class="badge">Verified</span>{% endif %}
        </div>
      </a>
    {% else %}
      <div class="empty-state wide-empty">No sellers match that search.</div>
    {% endfor %}
  </div>
</section>
{% endblock %}
