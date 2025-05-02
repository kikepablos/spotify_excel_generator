#!/usr/bin/env python3
"""
Spotify Excel Generator
Este script genera un archivo Excel con datos de 200 canciones de Spotify.
"""

import os
import time
import pandas as pd
from pandas.core.frame import console
import requests
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime
import numpy as np

# Importar librosa para análisis de audio
try:
    import librosa
except ImportError:
    print("La biblioteca librosa no está instalada. Instalando...")
    import subprocess
    subprocess.check_call(["pip3", "install", "librosa"])
    
# Importar bibliotecas para YouTube y audio
try:
    import pytube
    import yt_dlp
    import librosa
    import soundfile as sf
    import audioread
except ImportError:
    print("Instalando bibliotecas necesarias...")
    import subprocess
    subprocess.check_call(["pip3", "install", "pytube"])
    subprocess.check_call(["pip3", "install", "yt-dlp"])
    subprocess.check_call(["pip3", "install", "librosa"])
    subprocess.check_call(["pip3", "install", "soundfile"])
    subprocess.check_call(["pip3", "install", "audioread"])
    try:
        # Intentar importar después de la instalación
        import pytube
        import yt_dlp
        import librosa
        import soundfile as sf
        import audioread
    except ImportError as e:
        print(f"Error al importar después de la instalación: {e}")

# Verificar si FFmpeg está instalado
def check_ffmpeg():
    try:
        import shutil
        return shutil.which('ffmpeg') is not None
    except Exception:
        return False

# Intentar convertir un archivo de audio a formato WAV
def convert_to_wav(input_file, output_file=None):
    try:
        if output_file is None:
            output_file = os.path.splitext(input_file)[0] + ".wav"
        
        # Intentar usar FFmpeg si está disponible
        if check_ffmpeg():
            import subprocess
            print(f"Convirtiendo {input_file} a WAV usando FFmpeg...")
            subprocess.run(["ffmpeg", "-i", input_file, "-ar", "44100", "-ac", "2", output_file], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(output_file):
                return output_file
        
        # Si no hay FFmpeg, intentar con librosa
        print(f"Convirtiendo {input_file} a WAV usando librosa...")
        try:
            y, sr = librosa.load(input_file, sr=None)
            sf.write(output_file, y, sr)
            if os.path.exists(output_file):
                return output_file
        except Exception as e:
            print(f"Error al convertir con librosa: {e}")
        
        return None
    except Exception as e:
        print(f"Error al convertir archivo a WAV: {e}")
        return None

# Definir una función para analizar archivos de audio con librosa


# Cargar variables de entorno
load_dotenv()

# Configurar credenciales de Spotify
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
genius_token = os.getenv('GENIUS_ACCESS_TOKEN')

# Verificar si las credenciales están disponibles
if not client_id or not client_secret:
    print("Error: No se encontraron las credenciales de Spotify.")
    print("Por favor, crea un archivo .env con SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET.")
    exit(1)

# Inicializar cliente de Spotify
auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

def get_musical_key(key_number):
    """Convierte el número de clave musical a su representación en letra."""
    keys = {
        0: "C",
        1: "C#",
        2: "D",
        3: "D#",
        4: "E",
        5: "F",
        6: "F#",
        7: "G",
        8: "G#",
        9: "A",
        10: "A#",
        11: "B"
    }
    return keys.get(key_number, str(key_number))

def get_mode_name(mode):
    """Convierte el valor numérico del modo a su nombre."""
    return "Mayor" if mode == 1 else "Menor" if mode == 0 else str(mode)

def get_time_signature(signature):
    """Formatea la signatura de tiempo."""
    return f"{signature}/4" if signature else None

def get_lyrics_from_spotify_api(track_id):
    """
    Obtiene la letra de una canción usando la API de spotify-lyrics-api.
    
    Args:
        track_id (str): ID de la canción en Spotify
        
    Returns:
        str: Letra de la canción o mensaje de error
    """
    try:
        # URL de la API (usando una instancia pública de la API)
        api_url = f"https://spotify-lyric-api.herokuapp.com/?trackid={track_id}"
        
        # Realizar la solicitud
        response = requests.get(api_url, timeout=10)
        
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            data = response.json()
            
            # Verificar si hay error en la respuesta
            if data.get("error", True):
                return f"Error: {data.get('message', 'No se pudo obtener la letra')}"
            
            # Extraer las líneas de la letra
            lyrics_lines = []
            for line in data.get("lines", []):
                lyrics_lines.append(line.get("words", ""))
            
            # Unir las líneas en un solo texto
            lyrics = "\n".join(lyrics_lines)
            return lyrics
        
        # Manejar errores de la API
        elif response.status_code == 404:
            return "Letra no disponible para esta canción"
        else:
            return f"Error al obtener la letra: {response.status_code}"
    
    except Exception as e:
        print(f"Error al obtener la letra para la canción con ID {track_id}: {e}")
        return "Error al obtener la letra"

def search_song_lyrics(song_name, artist_name):
    """Busca la letra de una canción usando web scraping."""
    try:
        # Formatear la consulta para la búsqueda
        query = f"{song_name} {artist_name} lyrics"
        query = query.replace(' ', '+')
        
        # Realizar la búsqueda en Google
        search_url = f"https://www.google.com/search?q={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(search_url, headers=headers)
        
        if response.status_code != 200:
            return "No se pudo obtener la letra"
        
        # Buscar enlaces a sitios comunes de letras
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar enlaces a sitios de letras comunes
        lyrics_sites = ['azlyrics.com', 'genius.com', 'lyrics.com', 'musixmatch.com']
        lyrics_links = []
        
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'http' in href and any(site in href for site in lyrics_sites):
                for site in lyrics_sites:
                    if site in href:
                        lyrics_links.append(href)
                        break
        
        # Si encontramos enlaces, intentamos obtener la letra del primero
        if lyrics_links:
            # Extraer la URL real del enlace de Google
            lyrics_url = lyrics_links[0].split('&')[0].replace('/url?q=', '')
            
            # Obtener la página de letras
            lyrics_response = requests.get(lyrics_url, headers=headers)
            
            if lyrics_response.status_code == 200:
                lyrics_soup = BeautifulSoup(lyrics_response.text, 'html.parser')
                
                # Intentar diferentes selectores según el sitio
                lyrics_text = ""
                
                # Para AZLyrics
                if 'azlyrics.com' in lyrics_url:
                    lyrics_div = lyrics_soup.find('div', {'class': 'lyricsh'})
                    if lyrics_div:
                        lyrics_container = lyrics_div.find_next('div', {'class': None})
                        if lyrics_container:
                            lyrics_text = lyrics_container.get_text().strip()
                
                # Para Genius
                elif 'genius.com' in lyrics_url:
                    lyrics_div = lyrics_soup.find('div', {'class': 'lyrics'})
                    if lyrics_div:
                        lyrics_text = lyrics_div.get_text().strip()
                    else:
                        # Genius cambió su estructura HTML
                        lyrics_containers = lyrics_soup.find_all('div', {'data-lyrics-container': 'true'})
                        if lyrics_containers:
                            for container in lyrics_containers:
                                lyrics_text += container.get_text().strip() + "\n"
                
                # Para Musixmatch
                elif 'musixmatch.com' in lyrics_url:
                    lyrics_spans = lyrics_soup.find_all('span', {'class': 'lyrics__content__ok'})
                    if lyrics_spans:
                        for span in lyrics_spans:
                            lyrics_text += span.get_text().strip() + "\n"
                
                # Limpiar la letra
                lyrics_text = re.sub(r'\[.*?\]', '', lyrics_text)  # Eliminar [Verso], [Coro], etc.
                lyrics_text = re.sub(r'\n{3,}', '\n\n', lyrics_text)  # Reducir espacios en blanco excesivos
                
                if lyrics_text:
                    return lyrics_text[:2000]  # Limitar a 2000 caracteres para evitar textos muy largos
        
        return "No se pudo encontrar la letra"
    
    except Exception as e:
        print(f"Error al buscar la letra para {song_name} de {artist_name}: {e}")
        return "Error al obtener la letra"

def extract_track_data(track):
    """
    Extrae los datos relevantes de una canción de Spotify.
    
    Args:
        track (dict): Datos de la canción obtenidos de la API de Spotify
        
    Returns:
        dict: Diccionario con los datos procesados de la canción
    """
    # Obtener artistas
    artist_names = [artist['name'] for artist in track['artists']]
    artist_name = ", ".join(artist_names)
    
    # Obtener año de lanzamiento
    release_date = track['album']['release_date'] if 'album' in track and 'release_date' in track['album'] else None
    released_year = release_date.split('-')[0] if release_date else None
    
    # Obtener duración en formato mm:ss
    duration_ms = track['duration_ms']
    duration_sec = duration_ms / 1000
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    duration = f"{minutes}:{seconds:02d}"
    
    # Obtener ISRC si está disponible
    isrc = None
    if 'external_ids' in track and 'isrc' in track['external_ids']:
        isrc = track['external_ids']['isrc']
    
    # Crear diccionario con los datos procesados
    track_data = {
        'isrc': isrc,
        'id': track['id'],
        'track_name': track['name'],
        'artist_name': artist_name,
        'popularity': track['popularity'],
        'released_year': released_year,
        'duration': duration,
        'duration_ms': duration_ms,
        'album_name': track['album']['name'] if 'album' in track else None,
        'artist_id': track['artists'][0]['id'] if track['artists'] else None
    }
    
    return track_data

def enrich_tracks_with_audio_features(tracks):
    """Enriquece los datos de las canciones con características de audio."""
    print("Obteniendo características de audio para cada canción...")
    total_tracks = len(tracks)
    
    # Procesar canciones en lotes para las características de audio (máximo 100 por solicitud)
    batch_size = 50
    for i in range(0, total_tracks, batch_size):
        batch_end = min(i + batch_size, total_tracks)
        batch = tracks[i:batch_end]
        
        print(f"Procesando lote de características de audio {i+1}-{batch_end}/{total_tracks}...")
        
        # Obtener IDs de canciones en este lote
        track_ids = [track['id'] for track in batch]
        
        try:
            # Obtener características de audio para todo el lote
            audio_features_batch = sp.audio_features(track_ids)
            
            # Asignar características a cada canción
            for j, track in enumerate(batch):
                if j < len(audio_features_batch) and audio_features_batch[j]:
                    features = audio_features_batch[j]
                    
                    # Asignar valores a las columnas solicitadas
                    track['bpm'] = round(features['tempo'])
                    track['signature'] = get_time_signature(features['time_signature'])
                    track['loudness'] = round(features['loudness'], 2)
                    track['key'] = get_musical_key(features['key'])
                    track['mode'] = get_mode_name(features['mode'])
                    track['danceability'] = round(features['danceability'] * 100)
                    track['valence'] = round(features['valence'] * 100)
                    track['energy'] = round(features['energy'] * 100)
                    track['acousticness'] = round(features['acousticness'] * 100)
                    track['instrumentalness'] = round(features['instrumentalness'] * 100)
                    track['liveness'] = round(features['liveness'] * 100)
                    track['speechiness'] = round(features['speechiness'] * 100)
                else:
                    # Valores por defecto si no se pueden obtener las características
                    track['bpm'] = None
                    track['signature'] = None
                    track['loudness'] = None
                    track['key'] = None
                    track['mode'] = None
                    track['danceability'] = None
                    track['valence'] = None
                    track['energy'] = None
                    track['acousticness'] = None
                    track['instrumentalness'] = None
                    track['liveness'] = None
                    track['speechiness'] = None
        
        except Exception as e:
            print(f"Error al obtener características de audio para el lote {i}-{batch_end}: {e}")
            
            # Asignar valores por defecto para las canciones en este lote
            for track in batch:
                track['bpm'] = None
                track['signature'] = None
                track['loudness'] = None
                track['key'] = None
                track['mode'] = None
                track['danceability'] = None
                track['valence'] = None
                track['energy'] = None
                track['acousticness'] = None
                track['instrumentalness'] = None
                track['liveness'] = None
                track['speechiness'] = None
    
    return tracks

def get_artist_genres(artist_id):
    """Obtiene los géneros de un artista."""
    try:
        if not artist_id:
            return []
            
        artist = sp.artist(artist_id)
        return artist['genres']
    except Exception as e:
        print(f"Error al obtener géneros para el artista {artist_id}: {e}")
        return []

def enrich_tracks_with_genres(tracks):
    """Enriquece los datos de las canciones con géneros musicales."""
    print("Obteniendo géneros para cada canción...")
    total_tracks = len(tracks)
    
    for i, track in enumerate(tracks):
        # Mostrar progreso
        if i % 10 == 0:
            print(f"Procesando géneros de canción {i+1}/{total_tracks}...")
        
        # Obtener géneros del artista
        if 'artist_id' in track and track['artist_id']:
            genres = get_artist_genres(track['artist_id'])
            track['genre'] = ", ".join(genres) if genres else "No disponible"
        else:
            track['genre'] = "No disponible"
        
        # Esperar un poco para no sobrecargar la API
        time.sleep(0.1)
    
    return tracks

def enrich_tracks_with_lyrics(tracks):
    """Enriquece los datos de las canciones con letras."""
    print("Obteniendo letras para cada canción...")
    total_tracks = len(tracks)
    
    for i, track in enumerate(tracks):
        # Mostrar progreso
        if i % 10 == 0:
            print(f"Procesando letras de canción {i+1}/{total_tracks}...")
        
        # Obtener letra de la canción usando la API de Spotify
        if 'id' in track:
            lyrics = get_lyrics_from_spotify_api(track['id'])
            track['lyrics'] = lyrics
        else:
            track['lyrics'] = "No se pudo obtener la letra (ID no disponible)"
        
        # Esperar un poco para no sobrecargar las APIs
        time.sleep(1.5)
    
    return tracks

def create_excel(tracks, output_file='spotify_songs.xlsx'):
    """
    Crea un archivo Excel con los datos de las canciones.
    
    Args:
        tracks (list): Lista de diccionarios con información de las canciones
        output_file (str): Nombre del archivo Excel a crear
    """
    # Crear DataFrame con los datos
    df = pd.DataFrame(tracks)
    
    # Seleccionar y renombrar columnas
    columns = {
        'id': 'ID',
        'track_name': 'Nombre',
        'artist_name': 'Artista',
        'released_year': 'Año',
        'popularity': 'Popularidad',
        'duration': 'Duración',
        'bpm': 'BPM',
        'signature': 'Compás',
        'loudness': 'Volumen',
        'key': 'Tonalidad',
        'mode': 'Modo',
        'danceability': 'Bailabilidad',
        'valence': 'Valencia',
        'energy': 'Energía',
        'acousticness': 'Acústica',
        'instrumentalness': 'Instrumental',
        'liveness': 'En vivo',
        'speechiness': 'Hablado',
        'genre': 'Género',
        'lyrics': 'Letra',
        'album_name': 'Álbum'
    }
    
    # Seleccionar solo las columnas que existen en el DataFrame
    existing_columns = [col for col in columns.keys() if col in df.columns]
    df_selected = df[existing_columns].copy()
    
    # Renombrar columnas
    df_selected.rename(columns={col: columns[col] for col in existing_columns}, inplace=True)
    
    # Guardar en Excel
    df_selected.to_excel(output_file, index=False)
    
    print(f"Archivo Excel creado: {output_file}")
    print(f"Se han guardado datos de {len(tracks)} canciones.")

def get_spotify_access_token(client_id, client_secret):
    """
    Obtiene un token de acceso a la API de Spotify utilizando las credenciales de cliente.
    
    Args:
        client_id (str): ID de cliente de Spotify
        client_secret (str): Secreto de cliente de Spotify
        
    Returns:
        str: Token de acceso a la API de Spotify
    """
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'user-read-private user-read-email user-library-read playlist-read-private playlist-read-collaborative'
    })
    
    if auth_response.status_code != 200:
        print(f"Error al obtener token de acceso: {auth_response.status_code}")
        print(auth_response.text)
        return None
        
    auth_data = auth_response.json()
    return auth_data['access_token']

def get_playlist_tracks(playlist_id, access_token):
    """
    Obtiene las canciones de una playlist específica de Spotify.
    
    Args:
        playlist_id (str): ID de la playlist de Spotify
        access_token (str): Token de acceso a la API de Spotify
        
    Returns:
        dict: Respuesta de la API con los tracks de la playlist
    """
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error al obtener tracks de la playlist: {response.status_code}")
        print(response.text)
        return {'items': []}
        
    return response.json()

def get_featured_playlists(access_token, country='MX', limit=20):
    """
    Obtiene las playlists destacadas de Spotify.
    
    Args:
        access_token (str): Token de acceso a la API de Spotify
        country (str, optional): Código de país para filtrar playlists (ej. 'ES', 'US')
        limit (int, optional): Número máximo de playlists a obtener
        
    Returns:
        dict: Respuesta de la API con las playlists destacadas
    """
    url = f'https://api.spotify.com/v1/browse/featured-playlists'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'country': country,
        'limit': limit
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error al obtener playlists destacadas: {response.status_code}")
        print(response.text)
        return {'playlists': {'items': []}}
        
    return response.json()



def complete_excel_audio_features(excel_file='spotify_songs.xlsx'):
    """
    Lee un archivo Excel de canciones de Spotify y completa los campos de audio features que faltan.
    
    Args:
        excel_file (str): Ruta al archivo Excel a procesar
    """
    print(f"Leyendo archivo Excel: {excel_file}")
    
    # Verificar si el archivo existe
    if not os.path.exists(excel_file):
        print(f"Error: El archivo {excel_file} no existe.")
        return
    
    # Leer el archivo Excel
    df = pd.read_excel(excel_file)
    
    # Verificar si hay columna ID
    if 'ID' not in df.columns:
        print("Error: El archivo Excel no contiene la columna 'ID' necesaria para obtener las características de audio.")
        return
    
    # Mapeo de nombres de columnas en español a los nombres de la API
    column_mapping = {
        'Volumen': 'loudness',
        'Tonalidad': 'key',
        'Modo': 'mode',
        'Bailabilidad': 'danceability',
        'Valencia': 'valence',
        'Energía': 'energy',
        'Acústica': 'acousticness',
        'Instrumental': 'instrumentalness',
        'En vivo': 'liveness',
        'Hablado': 'speechiness'
    }
    
    # Obtener token de Spotify
    token = get_spotify_access_token(client_id, client_secret)
    if not token:
        print("Error: No se pudo obtener el token de acceso a Spotify.")
        return
    
    # Contador de filas actualizadas
    updated_rows = 0
    total_rows = len(df)
    
    # Procesar cada fila del DataFrame
    for index, row in df.iterrows():
        
        # Verificar si hay campos de audio features vacíos
        missing_features = True
        for spanish_name in column_mapping.keys():
            print(f"Verificando {spanish_name} para la fila {index+1}/{total_rows}")
            if spanish_name in df.columns and (pd.isna(row[spanish_name]) or row[spanish_name] == ''):
                missing_features = True
                break
        # print(f"Procesando fila {index+1}/{total_rows} id de cancion: {row['ID']}, missing features: {missing_features}")
        # Si no hay campos vacíos, continuar con la siguiente fila
        if not missing_features:
            continue
        
        # Obtener el ID de la canción
        track_id = row['ID']
        if pd.isna(track_id) or track_id == '':
            print(f"Advertencia: Fila {index+1} no tiene ID de canción, no se puede completar.")
            continue
        
        print(f"Procesando canción {index+1}/{total_rows}: {row.get('Nombre', 'Desconocido')}")
        
        # Obtener características de audio
        audio_features = get_audio_features(track_id, token)
        if not audio_features:
            print(f"No se pudieron obtener características de audio para la canción con ID: {track_id}")
            continue
        
        # Actualizar campos vacíos
        updated = False
        for spanish_name, api_name in column_mapping.items():
            if spanish_name in df.columns and (pd.isna(row[spanish_name]) or row[spanish_name] == ''):
                if api_name in audio_features and audio_features[api_name] is not None:
                    # Convertir el valor a tipo numérico si es necesario
                    try:
                        if api_name in ['danceability', 'energy', 'valence', 'acousticness', 
                                       'instrumentalness', 'liveness', 'speechiness', 'mode', 'loudness']:
                            value = float(audio_features[api_name])
                        else:
                            value = audio_features[api_name]
                        df.at[index, spanish_name] = value
                        updated = True
                    except (ValueError, TypeError):
                        # Si hay error en la conversión, usar el valor original
                        df.at[index, spanish_name] = audio_features[api_name]
                        updated = True
        
        if updated:
            updated_rows += 1
            
        # Esperar un poco para no sobrecargar la API
        time.sleep(1.5)
    
    # Guardar el DataFrame actualizado
    if updated_rows > 0:
        output_file = excel_file.replace('.xlsx', '_completado.xlsx')
        df.to_excel(output_file, index=False)
        print(f"Se actualizaron {updated_rows} canciones con datos de audio features.")
        print(f"Archivo Excel actualizado guardado como: {output_file}")
    else:
        print("No se encontraron filas para actualizar.")

def main(num_songs=20):
    token = get_spotify_access_token(client_id, client_secret)
    playlist_ids = [
        '5dnSFdz51E2Qouk7iFnwbl',
        '5KLKS1zjjeqSe6oRgsdUMb',
        '3BOQwadZjKpHajawvEO9T8',
        '4n5k7CWkhAubxdjP0qB9vC',   
    ]
    
    all_tracks = []
    track_ids_set = set()  # Para evitar duplicados
    
    for playlist_id in playlist_ids:
        tracks_res = get_playlist_tracks(playlist_id, token)
        for item in tracks_res['items']:
            if item['track'] and item['track']['id'] and item['track']['id'] not in track_ids_set:
                track_ids_set.add(item['track']['id'])
                all_tracks.append(item['track'])

    print(f"Se obtuvieron {len(all_tracks)} canciones de las playlists.")
    
    # Procesar y enriquecer las canciones
    processed_tracks = []
    # Limitar al número de canciones especificado
    limited_tracks = all_tracks[:num_songs]
    for track in limited_tracks:
        track_data = extract_track_data(track)

        # Obtener características de audio
        audio_features = get_audio_features(track['id'], token)
        track_data.update(audio_features)
        processed_tracks.append(track_data)
    print(processed_tracks)
    
    # Guardar en Excel
    create_excel(processed_tracks)


def main2():
    token = get_spotify_access_token(client_id, client_secret)
    
    print(audio_features)

if __name__ == "__main__":
    # letra = get_lyrics_from_spotify_api('45J4avUb9Ni0bnETYaYFVJ')
    # print(letra)
    token = get_spotify_access_token(client_id, client_secret)
    audio_features = get_audio_features('45J4avUb9Ni0bnETYaYFVJ', token)
    print(audio_features)
    # import sys
    
    # # # Verificar si se solicita completar un archivo Excel existente
    # if len(sys.argv) > 1 and sys.argv[1] == "completar":
    #     if len(sys.argv) > 2:
    #         excel_file = sys.argv[2]
    #         complete_excel_audio_features(excel_file)
    #     else:
    #         complete_excel_audio_features()
    # else:
    #     # Obtener el número de canciones desde los argumentos de línea de comandos
    #     num_songs = 20  # Valor predeterminado
    #     if len(sys.argv) > 1:
    #         try:
    #             num_songs = int(sys.argv[1])
    #             print(f"Generando Excel con {num_songs} canciones...")
    #         except ValueError:
    #             print("Error: El número de canciones debe ser un valor entero.")
    #             print("Usando el valor predeterminado: 20 canciones.")
        
    #     main(num_songs)
