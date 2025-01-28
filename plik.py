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
    layer_low = folium.FeatureGroup(name="Magnituda 4.5 - 4.9", show=False).add_to(m)
    layer_medium = folium.FeatureGroup(name="Magnituda 5.0 - 5.4", show=False).add_to(m)
    layer_high = folium.FeatureGroup(name="Magnituda 5.5+", show=False).add_to(m)

    # Funkcja klastrów
    marker_cluster = MarkerCluster(name="Wszystkie punkty", show=False).add_to(m)

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
        max_speed=100,  # Zwiększona szybkość timelapsa
        loop_button=True,
        date_options="YYYY-MM-DD",
        time_slider_drag_update=True,  # Przeciąganie suwaka
    ).add_to(m)

    # Dodanie Heatmapy jako dodatkowej warstwy
    HeatMap(heatmap_data, radius=15, blur=10, max_zoom=10).add_to(
        folium.FeatureGroup(name="Heatmapa", show=False).add_to(m)
    )

    # Dodanie MiniMapy
    MiniMap(toggle_display=True).add_to(m)

    # **Dodanie przycisku "Legenda" jako viewport**
    legend_html = """
    <style>
        #legend_button {
            position: fixed;
            bottom: calc(94vh + 20px); /* 10% od dolnej krawędzi + dodatkowy margines */
            left: 91vw; /* 2% szerokości ekranu od lewej */
            background-color: white;
            padding: 10px;
            border-radius: 5px;
            border: 2px solid black;
            cursor: pointer;
            font-weight: bold;
            z-index: 1000;
        }

        #legend_panel {
            position: fixed;
            bottom: calc(10vh + 50px);
            left: 2vw;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 10px;
            border: 2px solid black;
            display: none;
            font-size: 14px;
            z-index: 1000;
        }
    </style>

    <div id="legend_button" onclick="toggleLegend()">Legenda</div>

    <div id="legend_panel">
        <strong>Legenda:</strong><br>
        <i style="background: blue; width: 15px; height: 15px; display: inline-block; border-radius: 50%;"></i> Magnituda 4.5 - 4.9<br>
        <i style="background: green; width: 15px; height: 15px; display: inline-block; border-radius: 50%;"></i> Magnituda 5.0 - 5.4<br>
        <i style="background: red; width: 15px; height: 15px; display: inline-block; border-radius: 50%;"></i> Magnituda 5.5+<br>
        <div style="background: linear-gradient(to right, blue, red); width: 100px; height: 15px;"></div> Heatmapa - gęstość trzęsień ziemi
    </div>

    <script>
    function toggleLegend() {
        var panel = document.getElementById('legend_panel');
        if (panel.style.display === "none") {
            panel.style.display = "block";
        } else {
            panel.style.display = "none";
        }
    }
    </script>
    """

    m.get_root().html.add_child(folium.Element(legend_html))

    # Dodanie przycisku LayerControl do mapy
    folium.LayerControl().add_to(m)

    # Zapis mapy do pliku HTML
    output_file = "japan_earthquakes_with_responsive_legend.html"
    m.save(output_file)

    print(f"Mapa została zapisana w pliku {output_file}.")
except Exception as e:
    print(f"Wystąpił błąd: {e}")
