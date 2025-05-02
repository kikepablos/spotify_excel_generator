#!/usr/bin/env python3
"""
Spotify Excel Generator
Este script genera un archivo Excel con datos de canciones de Spotify.
Incluye funcionalidades para estimar características de audio cuando no están disponibles.
"""

import os
import sys
from dotenv import load_dotenv
from spotify_api import SpotifyAPI
from excel_manager import ExcelManager

def main(num_songs=20):
    """
    Función principal que genera un archivo Excel con datos de canciones de Spotify.
    
    Args:
        num_songs (int): Número de canciones a incluir en el Excel
    """
    # Inicializar API de Spotify
    spotify = SpotifyAPI()
    
    # Inicializar gestor de Excel
    excel = ExcelManager()
    
    # Lista de playlists de ejemplo
    playlist_ids = [
        '5dnSFdz51E2Qouk7iFnwbl',
        '5KLKS1zjjeqSe6oRgsdUMb',
        '3BOQwadZjKpHajawvEO9T8',
        '4n5k7CWkhAubxdjP0qB9vC',   
    ]
    
    # Obtener canciones de las playlists
    processed_tracks = spotify.get_tracks_from_playlists(playlist_ids, num_songs)
    # Crear archivo Excel
    excel.create_excel(processed_tracks)

def complete_excel(excel_file='spotify_songs.xlsx'):
    """
    Completa un archivo Excel existente con características de audio de Spotify.
    
    Args:
        excel_file (str): Ruta del archivo Excel a completar
    """
    # Inicializar API de Spotify
    spotify = SpotifyAPI()
    
    # Inicializar gestor de Excel
    excel = ExcelManager()
    
    # Preparar el DataFrame
    result = excel.complete_excel_audio_features(excel_file)
    
    if not result:
        return
    
    df, api_to_spanish, id_column = result
    
    # Actualizar cada canción
    updated_rows = 0
    
    for index, row in df.iterrows():
        track_id = row[id_column]
        
        if pd.isna(track_id):
            continue
        
        print(f"Procesando canción {index+1}/{len(df)}: ID {track_id}")
        
        # Obtener características de audio
        audio_features = spotify.get_audio_features(track_id)
        
        # Actualizar DataFrame
        updated = excel.update_excel_with_audio_features(df, track_id, audio_features, api_to_spanish, index)
        
        if updated:
            updated_rows += 1
        
        # Esperar un poco para no sobrecargar la API
        import time
        time.sleep(1.5)
    
    # Guardar DataFrame actualizado
    excel.save_updated_excel(df, excel_file, updated_rows)

def estimate_features_for_track(track_id):
    """
    Estima y muestra las características de audio de una canción específica.
    Útil para probar el algoritmo de estimación.
    
    Args:
        track_id (str): ID de la canción en Spotify
    """
    # Inicializar API de Spotify
    spotify = SpotifyAPI()
    
    # Obtener información de la canción
    try:
        track_info = spotify.sp.track(track_id)
        print(f"\nAnalizando canción: {track_info['name']} - {track_info['artists'][0]['name']}")
        print(f"Popularidad: {track_info['popularity']}/100")
        print(f"Álbum: {track_info['album']['name']} ({track_info['album']['release_date']})")
        print(f"Explícita: {'Sí' if track_info['explicit'] else 'No'}")
        
        # Obtener géneros del artista
        artist_id = track_info['artists'][0]['id']
        genres = spotify.get_artist_genres(artist_id)
        print(f"Géneros: {', '.join(genres) if genres else 'No disponibles'}")
        
        # Estimar características de audio
        print("\nCaracterísticas de audio estimadas:")
        estimated_features = spotify.estimate_audio_features(track_info)
        
        # Mostrar características estimadas
        print(f"Tempo (BPM): {estimated_features['tempo']:.1f}")
        print(f"Tonalidad: {estimated_features['key']}")
        print(f"Modo: {estimated_features['mode']}")
        print(f"Compás: {estimated_features['time_signature']}")
        print(f"Volumen: {estimated_features['loudness']:.1f} dB")
        print(f"Bailabilidad: {estimated_features['danceability']:.2f}")
        print(f"Energía: {estimated_features['energy']:.2f}")
        print(f"Valencia: {estimated_features['valence']:.2f}")
        print(f"Acústica: {estimated_features['acousticness']:.2f}")
        print(f"Instrumental: {estimated_features['instrumentalness']:.2f}")
        print(f"En vivo: {estimated_features['liveness']:.2f}")
        print(f"Hablado: {estimated_features['speechiness']:.2f}")
        
        # Intentar obtener características reales para comparar
        try:
            print("\nIntentando obtener características reales para comparar...")
            real_features = spotify.sp.audio_features(track_id)[0]
            if real_features:
                print("Características reales de la API de Spotify:")
                print(f"Tempo (BPM): {real_features['tempo']:.1f}")
                print(f"Tonalidad: {spotify.get_musical_key(real_features['key'])}")
                print(f"Modo: {spotify.get_mode_name(real_features['mode'])}")
                print(f"Compás: {spotify.get_time_signature(real_features['time_signature'])}")
                print(f"Volumen: {real_features['loudness']:.1f} dB")
                print(f"Bailabilidad: {real_features['danceability']:.2f}")
                print(f"Energía: {real_features['energy']:.2f}")
                print(f"Valencia: {real_features['valence']:.2f}")
                print(f"Acústica: {real_features['acousticness']:.2f}")
                print(f"Instrumental: {real_features['instrumentalness']:.2f}")
                print(f"En vivo: {real_features['liveness']:.2f}")
                print(f"Hablado: {real_features['speechiness']:.2f}")
        except Exception as e:
            print(f"No se pudieron obtener características reales: {e}")
    
    except Exception as e:
        print(f"Error al analizar la canción: {e}")

def compare_features(num_tracks=5):
    """
    Compara las características estimadas con las reales para varias canciones aleatorias.
    
    Args:
        num_tracks (int): Número de canciones a comparar
    """
    # Inicializar API de Spotify
    spotify = SpotifyAPI()
    
    # Obtener algunas playlists populares
    playlists = spotify.get_featured_playlists(limit=3)
    
    if 'playlists' not in playlists or 'items' not in playlists['playlists']:
        print("No se pudieron obtener playlists")
        return
    
    # Obtener tracks aleatorios de las playlists
    all_tracks = []
    for playlist in playlists['playlists']['items']:
        try:
            playlist_tracks = spotify.get_playlist_tracks(playlist['id'])
            if 'items' in playlist_tracks:
                all_tracks.extend([item['track'] for item in playlist_tracks['items'] if item.get('track')])
        except Exception as e:
            print(f"Error al obtener tracks de playlist {playlist['name']}: {e}")
    
    # Limitar al número solicitado
    import random
    if all_tracks:
        sample_tracks = random.sample(all_tracks, min(num_tracks, len(all_tracks)))
        
        for track in sample_tracks:
            estimate_features_for_track(track['id'])
            print("\n" + "-"*50 + "\n")
    else:
        print("No se pudieron obtener tracks para analizar")

def get_song_info_with_genius(song_name, artist_name):
    """
    Obtiene información de una canción utilizando la API de Genius.
    Muestra la letra completa y otros metadatos disponibles.
    
    Args:
        song_name (str): Nombre de la canción
        artist_name (str): Nombre del artista
    """
    # Inicializar API de Spotify
    spotify = SpotifyAPI()
    
    print(f"\nBuscando información para: {song_name} - {artist_name}")
    
    # Obtener información de la canción usando Genius
    song_info = spotify.get_song_info_from_genius(song_name, artist_name)
    
    # Mostrar resultados
    print("\nInformación obtenida:")
    print(f"Género: {song_info['genre']}")
    print(f"Álbum: {song_info['album']}")
    print(f"Fecha de lanzamiento: {song_info['release_date']}")
    
    # Mostrar letra (primeras líneas y últimas líneas)
    if song_info['lyrics'] != "No disponible":
        lyrics_lines = song_info['lyrics'].split('\n')
        
        if len(lyrics_lines) > 10:
            print("\nLetra (extracto):")
            # Mostrar primeras 5 líneas
            print('\n'.join(lyrics_lines[:5]))
            print("...")
            # Mostrar últimas 5 líneas
            print('\n'.join(lyrics_lines[-5:]))
            print(f"\n[Letra completa: {len(lyrics_lines)} líneas]")
        else:
            print("\nLetra:")
            print(song_info['lyrics'])
    else:
        print("\nLetra: No disponible")
    
    return song_info

def enrich_excel_with_genius_data(excel_file='spotify_songs.xlsx'):
    """
    Enriquece un archivo Excel existente con letras y géneros obtenidos de Genius.
    
    Args:
        excel_file (str): Ruta del archivo Excel a enriquecer
    """
    # Inicializar API de Spotify
    spotify = SpotifyAPI()
    
    # Inicializar gestor de Excel
    excel = ExcelManager()
    
    # Cargar el Excel
    import pandas as pd
    try:
        df = pd.read_excel(excel_file)
        print(f"Excel cargado correctamente: {len(df)} canciones encontradas.")
    except Exception as e:
        print(f"Error al cargar el archivo Excel: {e}")
        return
    
    # Verificar que existan las columnas necesarias
    required_columns = ['Nombre', 'Artista']
    for col in required_columns:
        if col not in df.columns:
            print(f"Error: Columna '{col}' no encontrada en el Excel.")
            return
    
    # Añadir columnas para letra y género si no existen
    if 'Letra' not in df.columns:
        df['Letra'] = ""
    if 'Género Detallado' not in df.columns:
        df['Género Detallado'] = ""
    
    # Procesar cada canción
    updated_rows = 0
    for index, row in df.iterrows():
        song_name = row['Nombre']
        artist_name = row['Artista']
        
        # Verificar si ya tiene letra y género
        if pd.notna(row['Letra']) and len(str(row['Letra'])) > 50 and pd.notna(row['Género Detallado']) and str(row['Género Detallado']) != "":
            print(f"Canción {index+1}/{len(df)}: {song_name} - {artist_name} ya tiene datos completos. Omitiendo.")
            continue
        
        print(f"\nProcesando canción {index+1}/{len(df)}: {song_name} - {artist_name}")
        
        # Obtener información de Genius
        song_info = spotify.get_song_info_from_genius(song_name, artist_name)
        
        # Inicializar variable de actualización
        updated = False
        
        # Actualizar DataFrame
        if song_info['lyrics'] != "No disponible" and (pd.isna(row['Letra']) or len(str(row['Letra'])) < 50):
            df.at[index, 'Letra'] = song_info['lyrics']
            updated = True
        
        if song_info['genre'] != "No disponible" and (pd.isna(row['Género Detallado']) or str(row['Género Detallado']) == ""):
            df.at[index, 'Género Detallado'] = song_info['genre']
            updated = True
        
        if updated:
            updated_rows += 1
            print(f"Datos actualizados para: {song_name} - {artist_name}")
        
        # Esperar un poco para no sobrecargar las APIs
        import time
        time.sleep(2)
    
    # Guardar Excel actualizado
    if updated_rows > 0:
        try:
            # Crear nombre para el nuevo archivo
            import os
            filename, ext = os.path.splitext(excel_file)
            new_file = f"{filename}_enriched{ext}"
            
            # Guardar el DataFrame
            df.to_excel(new_file, index=False)
            print(f"\nExcel actualizado guardado como: {new_file}")
            print(f"Se actualizaron {updated_rows} de {len(df)} canciones.")
        except Exception as e:
            print(f"Error al guardar el Excel actualizado: {e}")
    else:
        print("\nNo se realizaron actualizaciones en el Excel.")

def clean_df(excel_file='base de datosa canciones.xlsx'):
    """
    Limpia el DataFrame eliminando filas con valores faltantes.
    
    Args:
        excel_file (str): Ruta del archivo Excel a limpiar
        
    Returns:
        pd.DataFrame: DataFrame limpio sin ningún valor vacío
    """
    # Importar DataProcessor
    from data_processor import DataProcessor
    import pandas as pd
    
    processor = DataProcessor()
    
    # Cargar el DataFrame
    try:
        df = processor.load_from_excel(excel_file)
        print(f"\nDataFrame original: {len(df)} filas, {len(df.columns)} columnas")
        
        # Limpiar el DataFrame
        df_clean = processor.clean_dataframe(df)
        print(f"DataFrame después de limpieza básica: {len(df_clean)} filas, {len(df_clean.columns)} columnas")
        
        # Eliminar TODAS las filas que contengan algún valor vacío (NaN, None, o cadena vacía)
        # Primero reemplazar cadenas vacías con NaN para que dropna las detecte
        df_clean = df_clean.replace('', pd.NA)
        
        # Eliminar filas con cualquier valor faltante
        # Eliminar solo las filas con valores NA en la columna 'Letra'
        letra_col = 'Letra' if 'Letra' in df_clean.columns else 'lyrics'
        df_no_nulls = df_clean.dropna(subset=[letra_col])
        print(f"DataFrame sin valores vacíos en '{letra_col}': {len(df_no_nulls)} filas, {len(df_no_nulls.columns)} columnas")
        print(f"Se eliminaron {len(df_clean) - len(df_no_nulls)} filas con valores vacíos en '{letra_col}'")
        
        # Eliminar duplicados
        df_unique = processor.remove_duplicates(df_no_nulls)
        print(f"DataFrame sin duplicados: {len(df_unique)} filas, {len(df_unique.columns)} columnas")
        
        # Guardar el resultado
        output_file = "spotify_songs_cleaned.xlsx"
        processor.save_to_excel(df_unique, output_file)
        print(f"\nArchivo guardado como: {output_file}")
        
        return df_unique
        
    except FileNotFoundError:
        print(f"Error: El archivo '{excel_file}' no existe.")
        return None
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return None

if __name__ == "__main__":

    spotify = SpotifyAPI()

    # Verificar los argumentos de línea de comandos
    if len(sys.argv) > 1:
        # Caso: Estimar características para una canción específica
        if sys.argv[1] == "estimar" and len(sys.argv) > 2:
            track_id = sys.argv[2]
            estimate_features_for_track(track_id)
        
        # Caso: Comparar características estimadas vs reales
        elif sys.argv[1] == "comparar":
            num_tracks = 5
            if len(sys.argv) > 2:
                try:
                    num_tracks = int(sys.argv[2])
                except ValueError:
                    pass
            compare_features(num_tracks)
        
        # Caso: Completar un archivo Excel existente
        elif sys.argv[1] == "completar":
            if len(sys.argv) > 2:
                excel_file = sys.argv[2]
                complete_excel(excel_file)
            else:
                complete_excel()
        
        # Caso: Limpiar un archivo Excel existente
        elif sys.argv[1] == "limpiar":
            if len(sys.argv) > 2:
                excel_file = sys.argv[2]
                clean_df(excel_file)
            else:
                clean_df()
        
        # Caso: Generar Excel con número específico de canciones
        else:
            try:
                num_songs = int(sys.argv[1])
                print(f"Generando Excel con {num_songs} canciones...")
                main(num_songs)
            except ValueError:
                print("Error: El número de canciones debe ser un valor entero.")
                print("Usando el valor predeterminado: 20 canciones.")
                main(20)
    else:
        # Caso predeterminado: Generar Excel con 20 canciones
        main(20)




