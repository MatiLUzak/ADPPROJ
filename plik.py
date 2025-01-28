import folium
from folium.plugins import TimestampedGeoJson, MarkerCluster, HeatMap, MiniMap
import geopandas as gpd
import pandas as pd
from branca.element import Template, MacroElement

# Ścieżka do pliku GeoJSON
geojson_file = "query.geojson"

try:
    # Wczytanie pliku GeoJSON
    data = gpd.read_file(geojson_file)

    # Konwersja kolumny `time` na format daty
    data["time"] = pd.to_datetime(data["time"], unit="ms")

    # Utworzenie mapy
    m = folium.Map(location=[36.2048, 138.2529], zoom_start=5, tiles="CartoDB Positron")

    # Warstwy dla filtrowania
    layer_low = folium.FeatureGroup(name="Magnituda 4.5 - 4.9").add_to(m)
    layer_medium = folium.FeatureGroup(name="Magnituda 5.0 - 5.4").add_to(m)
    layer_high = folium.FeatureGroup(name="Magnituda 5.5+").add_to(m)

    # Funkcja klastrów
    marker_cluster = MarkerCluster(name="Wszystkie punkty").add_to(m)

    # Lista danych do heatmapy i timelapsa
    heatmap_data = []
    features = []

    # Tworzenie punktów i filtrowanie danych
    for _, row in data.iterrows():
        mag = row["mag"]  # Magnituda
        time = row["time"].isoformat()  # Data w formacie ISO8601
        coords = row["geometry"].coords[0]  # Współrzędne (lon, lat)
        popup_text = f"""
        <strong>Magnituda:</strong> {mag}<br>
        <strong>Miejsce:</strong> {row.get('place', 'Brak informacji')}<br>
        <a href="{row.get('url', '#')}" target="_blank">Szczegóły</a>
        """

        # Wybór koloru i warstwy na podstawie magnitudy
        if 4.5 <= mag < 5.0:
            color = "blue"
            layer = layer_low
        elif 5.0 <= mag < 5.5:
            color = "green"
            layer = layer_medium
        else:  # mag >= 5.5
            color = "red"
            layer = layer_high

        # Dodanie punktu do odpowiedniej warstwy
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=popup_text,
        ).add_to(layer)

        # Dodanie punktu do klastrów
        folium.CircleMarker(
            location=[coords[1], coords[0]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=popup_text,
        ).add_to(marker_cluster)

        # Dodanie danych do heatmapy
        heatmap_data.append([coords[1], coords[0], mag])

        # Dodanie punktu do TimestampedGeoJson
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [coords[0], coords[1]],
            },
            "properties": {
                "time": time,
                "style": {"color": color},
                "icon": "circle",
                "popup": popup_text,
            },
        }
        features.append(feature)

    # Utworzenie obiektu GeoJSON dla suwaka czasowego
    timestamped_geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    # Dodanie TimestampedGeoJson do mapy
    TimestampedGeoJson(
        data=timestamped_geojson,
        period="P1D",  # Przesunięcie o 1 dzień
        add_last_point=True,
        auto_play=False,
        loop=False,
        max_speed=10,  # Przyspieszone odtwarzanie timelapsa
        loop_button=True,
        date_options="YYYY-MM-DD",
        time_slider_drag_update=True,  # Przeciąganie suwaka
    ).add_to(m)

    # Dodanie Heatmapy jako dodatkowej warstwy
    HeatMap(heatmap_data, radius=15, blur=10, max_zoom=10).add_to(
        folium.FeatureGroup(name="Heatmapa").add_to(m)
    )

    # Dodanie MiniMapy
    MiniMap(toggle_display=True).add_to(m)

    # Dodanie legendy
    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 250px;
        height: 120px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:14px;
        padding: 10px;
        ">
        <strong>Legenda:</strong><br>
        <i style="background: blue; width: 10px; height: 10px; float: left; margin-right: 5px; opacity: 0.7;"></i>
        Magnituda 4.5 - 4.9<br>
        <i style="background: green; width: 10px; height: 10px; float: left; margin-right: 5px; opacity: 0.7;"></i>
        Magnituda 5.0 - 5.4<br>
        <i style="background: red; width: 10px; height: 10px; float: left; margin-right: 5px; opacity: 0.7;"></i>
        Magnituda 5.5+<br>
    </div>
    """
    legend = MacroElement()
    legend._template = Template(legend_html)
    m.get_root().add_child(legend)

    # Dodanie przycisku LayerControl do mapy
    folium.LayerControl().add_to(m)

    # Zapis mapy do pliku HTML
    output_file = "japan_earthquakes_with_fast_timeline.html"
    m.save(output_file)

    print(f"Mapa została zapisana w pliku {output_file}.")
except Exception as e:
    print(f"Wystąpił błąd: {e}")
