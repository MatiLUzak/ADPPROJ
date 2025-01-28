import folium
from folium.plugins import TimestampedGeoJson, MarkerCluster, HeatMap, MiniMap
import geopandas as gpd
import pandas as pd

# Ścieżka do pliku GeoJSON
geojson_file = "query.geojson"

try:
    # Wczytanie pliku GeoJSON
    data = gpd.read_file(geojson_file)

    # Konwersja kolumny `time` na format daty
    data["time"] = pd.to_datetime(data["time"], unit="ms")

    # Utworzenie mapy
    m = folium.Map(location=[36.2048, 138.2529], zoom_start=5, tiles="CartoDB Positron")

    # Dodanie funkcji klastrów
    marker_cluster = MarkerCluster().add_to(m)

    # Utworzenie listy funkcji GeoJSON dla TimestampedGeoJson
    features = []
    heatmap_data = []  # Dane do heatmapy
    for _, row in data.iterrows():
        mag = row["mag"]  # Magnituda
        time = row["time"].isoformat()  # Data w formacie ISO8601
        coords = row["geometry"].coords[0]  # Współrzędne (lon, lat)
        popup_text = f"""
        <strong>Magnituda:</strong> {mag}<br>
        <strong>Miejsce:</strong> {row.get('place', 'Brak informacji')}<br>
        <a href="{row.get('url', '#')}" target="_blank">Szczegóły</a>
        """

        # Wybór koloru na podstawie magnitudy
        if 4.5 <= mag < 5.0:
            color = "blue"
        elif 5.0 <= mag < 5.5:
            color = "green"
        else:  # mag >= 6.0
            color = "red"

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
        max_speed=1,
        loop_button=True,
        date_options="YYYY-MM-DD",
        time_slider_drag_update=True,
    ).add_to(m)

    # Dodanie Heatmapy jako dodatkowej warstwy
    HeatMap(heatmap_data, radius=15, blur=10, max_zoom=10).add_to(m)

    # Dodanie MiniMapy
    minimap = MiniMap(toggle_display=True)
    minimap.add_to(m)

    # Dodanie skali (alternatywna metoda)
    folium.map.LayerControl().add_to(m)

    # Zapis mapy do pliku HTML
    output_file = "japan_earthquakes_timeline_with_clusters_and_features.html"
    m.save(output_file)

    print(f"Mapa została zapisana w pliku {output_file}.")
except Exception as e:
    print(f"Wystąpił błąd: {e}")
