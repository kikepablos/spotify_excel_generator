#!/usr/bin/env python3
"""
Módulo para interactuar con la API de Spotify
"""

import os
import time
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import numpy as np
import librosa
import soundfile as sf
import yt_dlp
import pytube
import audioread
import subprocess
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

class SpotifyAPI:
    def __init__(self, client_id=None, client_secret=None):
        """
        Inicializa la clase SpotifyAPI con las credenciales de Spotify.
        
        Args:
            client_id (str): ID de cliente de Spotify
            client_secret (str): Secreto de cliente de Spotify
        """
        # Cargar variables de entorno si no se proporcionan credenciales
        if client_id is None or client_secret is None:
            load_dotenv()
            self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
            self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            self.genius_token = os.getenv('GENIUS_ACCESS_TOKEN')
        else:
            self.client_id = client_id
            self.client_secret = client_secret
            self.genius_token = None
        
        # Verificar que las credenciales estén disponibles
        if not self.client_id or not self.client_secret:
            raise ValueError("Las credenciales de Spotify no están configuradas. Configura las variables de entorno SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET.")
        
        # Inicializar cliente de Spotify
        self.auth_manager = SpotifyClientCredentials(client_id=self.client_id, client_secret=self.client_secret)
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
        
        # Obtener token de acceso
        self.access_token = self.get_spotify_access_token()
    
    def get_spotify_access_token(self):
        """
        Obtiene un token de acceso a la API de Spotify utilizando las credenciales de cliente.
        
        Returns:
            str: Token de acceso a la API de Spotify
        """
        auth_url = 'https://accounts.spotify.com/api/token'
        auth_response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
        
        # Verificar si la solicitud fue exitosa
        if auth_response.status_code != 200:
            raise Exception(f"Error al obtener token de acceso: {auth_response.status_code} - {auth_response.text}")
        
        # Extraer token de la respuesta
        auth_data = auth_response.json()
        return auth_data['access_token']
    
    def get_playlist_tracks(self, playlist_id):
        """
        Obtiene las canciones de una playlist específica de Spotify.
        
        Args:
            playlist_id (str): ID de la playlist de Spotify
            
        Returns:
            dict: Respuesta de la API con los tracks de la playlist
        """
        endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        response = requests.get(endpoint, headers=headers)
        
        # Verificar si la solicitud fue exitosa
        if response.status_code != 200:
            raise Exception(f"Error al obtener tracks de la playlist: {response.status_code} - {response.text}")
        return response.json()
    
    def get_featured_playlists(self, country='MX', limit=20):
        """
        Obtiene las playlists destacadas de Spotify.
        
        Args:
            country (str, optional): Código de país para filtrar playlists (ej. 'ES', 'US')
            limit (int, optional): Número máximo de playlists a obtener
            
        Returns:
            dict: Respuesta de la API con las playlists destacadas
        """
        endpoint = "https://api.spotify.com/v1/browse/featured-playlists"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        params = {
            "country": country,
            "limit": limit
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        
        # Verificar si la solicitud fue exitosa
        if response.status_code != 200:
            raise Exception(f"Error al obtener playlists destacadas: {response.status_code} - {response.text}")
        
        return response.json()
    
    def get_audio_features(self, track):
        """
        Obtiene las características de audio de una canción específica de Spotify.
        Utiliza Librosa para extraer directamente las características de audio del archivo de preview.
        Si no se pueden obtener las características reales, las estima basándose en el género y popularidad.
        
        Args:
            track_id (str): ID de la canción en Spotify
            
        Returns:
            dict: Características de audio de la canción
        """
        try:
            # Primero intentar obtener características de audio mediante la API de Spotify
            
            # Inicializar diccionario de resultados con datos de la API
            result = {
                'danceability': None,
                'energy': None,
                'key': None,
                'loudness': None,
                'mode': None,
                'speechiness': None,
                'acousticness': None,
                'instrumentalness': None,
                'liveness': None,
                'valence': None,
                'tempo': None,
                'time_signature': None,
                'duration_ms': None,
                'duration_min': None,
                'lyrics': None
            }
            preview_url = track.get('preview_url')
            track_id = track.get('id')
            # Si hay una URL de preview, intentar descargar y analizar
            if preview_url:
                try:
                    # Crear directorio temporal si no existe
                    temp_dir = 'temp_audio'
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Descargar el archivo de preview
                    preview_file = os.path.join(temp_dir, f"{track_id}_preview.mp3")
                    response = requests.get(preview_url)
                    with open(preview_file, 'wb') as f:
                        f.write(response.content)
                    
                    # Analizar el archivo de audio
                    audio_analysis = self.analyze_audio_file(preview_file, track_info)
                    if audio_analysis:
                        # Actualizar resultado con datos del análisis
                        result.update(audio_analysis)
                    
                    # Limpiar archivos temporales
                    if os.path.exists(preview_file):
                        os.remove(preview_file)
                
                except Exception as e:
                    print(f"Error al analizar preview de audio: {e}")
            
            # Intentar obtener letra de la canción
            artist_name = track_info['artists'][0]['name']
            track_name = track_info['name']
            track_lyrics = self.get_song_lyrics_from_genius(track_name, artist_name)
            result['lyrics'] = track_lyrics['lyrics']
            return result
        
        except Exception as e:
            print(f"Error al obtener características de audio: {e}")
            # Intentar estimar características basadas en metadatos
            try:
                track_info = self.sp.track(track_id)
                return self.estimate_audio_features(track_info)
            except Exception as e:
                print(f"Error al estimar características: {e}")
                return {
                    'danceability': None,
                    'energy': None,
                    'key': None,
                    'loudness': None,
                    'mode': None,
                    'speechiness': None,
                    'acousticness': None,
                    'instrumentalness': None,
                    'liveness': None,
                    'valence': None,
                    'tempo': None,
                    'time_signature': None,
                    'duration_ms': None,
                    'duration_min': None,
                    'lyrics': "No disponible"
                }
    
    def get_musical_key(self, key_number):
        """
        Convierte el número de clave musical a su representación en letra.
        
        Args:
            key_number (int): Número de clave musical (0-11)
            
        Returns:
            str: Representación en letra de la clave musical
        """
        if key_number is None:
            return "Desconocido"
        
        keys = {
            0: "C",
            1: "C♯/D♭",
            2: "D",
            3: "D♯/E♭",
            4: "E",
            5: "F",
            6: "F♯/G♭",
            7: "G",
            8: "G♯/A♭",
            9: "A",
            10: "A♯/B♭",
            11: "B"
        }
        return keys.get(key_number, "Desconocido")
    
    def get_mode_name(self, mode):
        """
        Convierte el valor numérico del modo a su nombre.
        """
        return "Mayor" if mode == 1 else "Menor" if mode == 0 else "Desconocido"
    
    def get_time_signature(self, signature):
        """
        Formatea la signatura de tiempo.
        """
        return f"{signature}/4" if signature else "Desconocido"
    
    def get_lyrics_from_spotify_api(self, track_id):
        """
        Obtiene la letra de una canción usando la API de spotify-lyrics-api.
        
        Args:
            track_id (str): ID de la canción en Spotify
            
        Returns:
            str: Letra de la canción o mensaje de error
        """
        try:
            # Usar la API no oficial de letras de Spotify
            lyrics_url = f"https://spotify-lyric-api.herokuapp.com/?trackid={track_id}"
            response = requests.get(lyrics_url)
            
            if response.status_code != 200:
                return "No se pudo obtener la letra (Error en la API)"
            
            lyrics_data = response.json()
            
            # Verificar si hay un error en la respuesta
            if "error" in lyrics_data:
                return f"No se pudo obtener la letra ({lyrics_data['error']})"
            
            # Extraer y formatear la letra
            formatted_lyrics = ""
            for line in lyrics_data.get("lines", []):
                formatted_lyrics += line.get("words", "") + "\n"
            
            if not formatted_lyrics:
                return "Letra no disponible"
            
            return formatted_lyrics
        
        except Exception as e:
            print(f"Error al obtener letra de la API: {e}")
            return "Error al obtener letra"
    
    def search_song_lyrics(self, song_name, artist_name):
        """
        Busca la letra de una canción usando web scraping.
        
        Args:
            song_name (str): Nombre de la canción
            artist_name (str): Nombre del artista
            
        Returns:
            str: Letra de la canción o mensaje de error
        """
        try:
            # Limpiar nombres para la búsqueda
            song_search = song_name.lower().replace(' ', '+')
            artist_search = artist_name.lower().replace(' ', '+')
            
            # Intentar buscar en Google
            search_query = f"{song_search}+{artist_search}+lyrics"
            search_url = f"https://www.google.com/search?q={search_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers)
            
            if response.status_code != 200:
                return "No se pudo buscar la letra"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar la letra en los resultados de Google
            lyrics_div = soup.find('div', class_='ujudUb')
            
            if lyrics_div:
                # Extraer y formatear la letra
                lyrics_text = lyrics_div.get_text(separator='\n')
                
                # Limpiar la letra
                lyrics_text = re.sub(r'\[.*?\]', '', lyrics_text)  # Eliminar etiquetas como [Verso], [Coro], etc.
                lyrics_text = re.sub(r'\n{3,}', '\n\n', lyrics_text)  # Reducir múltiples saltos de línea
                
                return lyrics_text.strip()
            
            # Si no se encuentra en Google, intentar con otras fuentes
            # Aquí se podrían agregar más fuentes como AZLyrics, Genius, etc.
            
            return "Letra no encontrada"
        
        except Exception as e:
            print(f"Error al buscar letra: {e}")
            return "Error al buscar letra"
            
    def get_song_lyrics_from_genius(self, song_name, artist_name):
        """
        Obtiene la letra de una canción utilizando la API de Genius a través de lyricsgenius.
        
        Args:
            song_name (str): Nombre de la canción
            artist_name (str): Nombre del artista
            
        Returns:
            dict: Diccionario con la información de la canción (letra, género, etc.)
        """
        try:
            # Inicializar diccionario de resultados
            # song_info = {
            #     'lyrics': "No disponible",
            #     'genre': "No disponible",
            #     'album': "No disponible",
            #     'release_date': "No disponible",
            #     'writer': "No disponible",
            #     'producer': "No disponible"
            # }
            
            # Importar lyricsgenius
            import lyricsgenius
            
            # Configurar el cliente de Genius
            # Intentar obtener el token desde variables de entorno
            import os
            genius_token = os.getenv('GENIUS_ACCESS_TOKEN')
            
            # # Si no hay token, intentar obtener la letra de otra manera
            # if not genius_token:
            #     print("No se ha encontrado token de Genius API en variables de entorno. Usando método alternativo.")
            #     return self.get_song_info_alternate(song_name, artist_name)
            
            # Inicializar el cliente de Genius
            genius = lyricsgenius.Genius(genius_token, timeout=15, retries=3)
            genius.verbose = False  # Desactivar mensajes de depuración
            
            print(f"Buscando información para: {song_name} - {artist_name}")
            # Buscar la canción en Genius
            try:
                song = genius.search_song(song_name, artist_name)
                if song:
                    # Extraer la letra
                    song_info['lyrics'] = song.lyrics
                    print("Letra encontrada en Genius")
                    
                    # Extraer metadatos adicionales si están disponibles
                    if hasattr(song, 'album') and song.album:
                        song_info['album'] = song.album
                    
                    if hasattr(song, 'year') and song.year:
                        song_info['release_date'] = song.year
                    
                    # Intentar obtener género a través de la API de Spotify
                    try:
                        # Buscar la canción en Spotify para obtener más metadatos
                        search_results = self.sp.search(q=f"track:{song_name} artist:{artist_name}", type='track', limit=1)
                        if search_results and search_results['tracks']['items']:
                            track = search_results['tracks']['items'][0]
                            
                            # Obtener género del artista
                            if track['artists'] and len(track['artists']) > 0:
                                artist_id = track['artists'][0]['id']
                                artist_info = self.sp.artist(artist_id)
                                if 'genres' in artist_info and artist_info['genres']:
                                    song_info['genre'] = ', '.join(artist_info['genres'])
                                    print(f"Género encontrado: {song_info['genre']}")
                            
                            # Obtener información del álbum
                            if 'album' in track and track['album']:
                                if 'name' in track['album']:
                                    song_info['album'] = track['album']['name']
                                if 'release_date' in track['album']:
                                    song_info['release_date'] = track['album']['release_date']
                    except Exception as e:
                        print(f"Error al obtener metadatos adicionales de Spotify: {e}")
            except Exception as e:
                print(f"Error al buscar en Genius: {e}")
                error_text = str(e)
                lyrics = None
                lyrics_url = None
                if 'url: ' in error_text:
                    error_url = error_text.split('url: ')[1].strip("'")
                
                # Verificar si la URL contiene JSON con lyric_url
                try:
                    response = requests.get(error_url, timeout=10)
                    if response.status_code == 200:
                        json_data = response.json()
                        top_hit = json_data['response']['sections'][0]['hits'][0]['result']
                        song_name = top_hit.get('title', 'Unknown')
                        artist_name = top_hit.get('primary_artist', {}).get('name', 'Unknown')
                        lyrics_url = top_hit.get('url', 'Unknown')
                        lyrics = self.extract_lyrics_from_genius_url(lyrics_url)
                        genre = 'Unknown'  # No viene en el JSON, así que default
                        
                except Exception as json_error:
                    print(f"Error al procesar JSON de la URL: {json_error}")
            # extracted_lyrics = self.extract_lyrics_from_genius_url(error_url)
            return {
                'error_url': error_url,
                'lyrics': lyrics,
                'lyrics_url': lyrics_url
            }
            
            
        except Exception as e:
            print(f"Error general al obtener información de la canción: {e}")
            # Extraer la URL del error
          
    
    def extract_lyrics_from_genius_url(self, url):
        """
        Extrae la letra de una canción directamente desde una URL de Genius.
        
        Args:
            url (str): URL de Genius con la letra de la canción (ej: https://genius.com/The-weeknd-blinding-lights-lyrics)
            
        Returns:
            str: Letra de la canción o mensaje de error si no se pudo extraer
        """
        try:
            # Configurar encabezados para simular un navegador real
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
            }
            
            print(f"Extrayendo letra desde URL de Genius: {url}")
            
            # Realizar la solicitud a Genius
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Error en la solicitud: {response.status_code}")
                return "No se pudo obtener la letra: error en la solicitud"
            
            # Parsear el HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Método 1: Buscar todos los contenedores de letra con el atributo data-lyrics-container
            lyrics_containers = soup.select('div[data-lyrics-container="true"]')
            if lyrics_containers:
                full_lyrics = []
                for container in lyrics_containers:
                    # Reemplazar <br> por saltos de línea
                    for br in container.find_all('br'):
                        br.replace_with('\n')
                    
                    # Obtener el texto y añadirlo a la lista
                    container_text = container.get_text()
                    if container_text.strip():
                        full_lyrics.append(container_text.strip())
                
                if full_lyrics:
                    # Unir las partes de la letra
                    raw_lyrics = '\n\n'.join(full_lyrics)
                    
                    # Limpiar la letra: eliminar metadatos y texto que no forma parte de la letra
                    # Buscar el primer corchete que indica el inicio de la letra ([Verse], [Intro], etc.)
                    lyrics_start = re.search(r'\[.*?\]', raw_lyrics)
                    if lyrics_start:
                        # Extraer solo desde el primer corchete
                        clean_lyrics = raw_lyrics[lyrics_start.start():]
                        print("Letra extraída y limpiada con éxito")
                        return clean_lyrics
                    else:
                        # Si no hay corchetes, intentar limpiar de otra manera
                        # Eliminar líneas que parecen metadatos (contribuidores, traducciones, etc.)
                        lines = raw_lyrics.split('\n')
                        filtered_lines = []
                        lyrics_started = False
                        
                        for line in lines:
                            # Ignorar líneas que parecen metadatos
                            if any(keyword in line for keyword in ['Contributors', 'Translations', 'Lyrics', 'Read More']):
                                continue
                            
                            # Una vez que encontramos una línea que parece parte de la letra, comenzamos a guardar
                            if line.strip() and not lyrics_started:
                                lyrics_started = True
                            
                            if lyrics_started:
                                filtered_lines.append(line)
                        
                        if filtered_lines:
                            print("Letra extraída y filtrada con éxito")
                            return '\n'.join(filtered_lines)
                        else:
                            print("No se pudo filtrar adecuadamente la letra")
                            return raw_lyrics
            
            # Método 2: Extraer directamente el HTML y buscar secciones de la letra
            html_content = response.text
            
            # Buscar secciones que parezcan versos
            # Buscar texto entre corchetes como [Verse], [Chorus], etc.
            lyrics_pattern = re.compile(r'(\[.*?\][\s\S]*?)(?=\[|$)')
            sections = lyrics_pattern.findall(html_content)
            
            if sections:
                # Limpiar HTML de las secciones
                cleaned_sections = []
                for section in sections:
                    # Eliminar etiquetas HTML
                    section_soup = BeautifulSoup(section, 'html.parser')
                    section_text = section_soup.get_text().strip()
                    
                    # Verificar que la sección parece ser parte de la letra
                    if section_text.startswith('[') and len(section_text) > 10:
                        cleaned_sections.append(section_text)
                
                if cleaned_sections:
                    lyrics = '\n\n'.join(cleaned_sections)
                    print("Letra extraída con éxito usando patrón de secciones")
                    return lyrics
            
            # Método 3: Buscar en la estructura DOM
            # Intentar encontrar el contenedor principal de la letra
            lyrics_div = soup.select_one('div.lyrics')
            if lyrics_div:
                # Reemplazar <br> por saltos de línea
                for br in lyrics_div.find_all('br'):
                    br.replace_with('\n')
                
                lyrics = lyrics_div.get_text()
                # Limpiar la letra
                lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)  # Reducir múltiples saltos de línea
                print("Letra extraída con éxito usando div.lyrics")
                return lyrics.strip()
            
            # Método 4: Buscar cualquier elemento que pueda contener la letra
            # Buscar elementos con clases que suelen contener letras
            potential_containers = soup.select('.lyrics, .Lyrics__Container, .SongPageGrid-sc-1vi6xda-0')
            if potential_containers:
                for container in potential_containers:
                    # Reemplazar <br> por saltos de línea
                    for br in container.find_all('br'):
                        br.replace_with('\n')
                    
                    text = container.get_text()
                    # Verificar si parece una letra (contiene corchetes o tiene más de 100 caracteres)
                    if '[' in text or len(text) > 100:
                        # Limpiar la letra
                        text = re.sub(r'\n{3,}', '\n\n', text)  # Reducir múltiples saltos de línea
                        print("Letra extraída con éxito usando contenedor potencial")
                        return text.strip()
            
            print("No se pudo encontrar la letra con ningún método")
            return "No se pudo extraer la letra: contenido no encontrado"
                
        except Exception as e:
            print(f"Error al extraer letra desde Genius: {e}")
            return f"Error al extraer letra: {str(e)}"
    
    def get_song_info_alternate(self, song_name, artist_name):
        """
        Método alternativo para obtener información de canciones cuando Genius API no está disponible.
        Utiliza AZLyrics o otras fuentes alternativas.
        
        Args:
            song_name (str): Nombre de la canción
            artist_name (str): Nombre del artista
            
        Returns:
            dict: Diccionario con la información de la canción (letra, género, etc.)
        """
        try:
            # Inicializar diccionario de resultados
            song_info = {
                'lyrics': "No disponible",
                'genre': "No disponible",
                'album': "No disponible",
                'release_date': "No disponible",
                'writer': "No disponible",
                'producer': "No disponible"
            }
            
            # Limpiar nombres para la búsqueda
            artist_clean = artist_name.lower().replace(' ', '')
            song_clean = song_name.lower().replace(' ', '')
            
            # Intentar obtener letra de AZLyrics (formato de URL predecible)
            azlyrics_url = f"https://www.azlyrics.com/lyrics/{artist_clean}/{song_clean}.html"
            
            # Configurar encabezados para simular un navegador real
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://www.google.com/'
            }
            
            print(f"Intentando obtener letra desde AZLyrics para: {song_name} - {artist_name}")
            
            try:
                # Esperar un poco para evitar ser bloqueado
                import time
                time.sleep(2)
                
                response = requests.get(azlyrics_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # En AZLyrics, la letra está en una div sin clase pero con un patrón reconocible
                    lyrics_div = soup.find('div', {'class': None, 'id': None}, text=lambda t: t and t.strip())
                    if lyrics_div and not lyrics_div.find('div'):
                        # Encontrar el div correcto que contiene la letra
                        for div in soup.find_all('div', {'class': None, 'id': None}):
                            if div.text.strip() and not div.find('div') and len(div.text.strip()) > 100:
                                song_info['lyrics'] = div.text.strip()
                                print("Letra encontrada en AZLyrics")
                                break
            except Exception as e:
                print(f"Error al obtener letra desde AZLyrics: {e}")
            
            # Si no se encontró la letra, intentar con Musixmatch
            if song_info['lyrics'] == "No disponible":
                try:
                    # Formatear para Musixmatch
                    artist_mm = artist_name.lower().replace(' ', '-')
                    song_mm = song_name.lower().replace(' ', '-')
                    
                    musixmatch_url = f"https://www.musixmatch.com/lyrics/{artist_mm}/{song_mm}"
                    
                    # Esperar un poco para evitar ser bloqueado
                    time.sleep(2)
                    
                    response = requests.get(musixmatch_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # En Musixmatch, la letra está en divs con clase 'mxm-lyrics__content'
                        lyrics_divs = soup.find_all('span', {'class': 'lyrics__content__ok'})
                        if lyrics_divs:
                            lyrics = '\n'.join([div.text.strip() for div in lyrics_divs])
                            song_info['lyrics'] = lyrics
                            print("Letra encontrada en Musixmatch")
                except Exception as e:
                    print(f"Error al obtener letra desde Musixmatch: {e}")
            
            # Intentar obtener metadatos de Spotify
            try:
                # Buscar la canción en Spotify
                search_results = self.sp.search(q=f"track:{song_name} artist:{artist_name}", type='track', limit=1)
                if search_results and search_results['tracks']['items']:
                    track = search_results['tracks']['items'][0]
                    
                    # Obtener género del artista
                    if track['artists'] and len(track['artists']) > 0:
                        artist_id = track['artists'][0]['id']
                        artist_info = self.sp.artist(artist_id)
                        if 'genres' in artist_info and artist_info['genres']:
                            song_info['genre'] = ', '.join(artist_info['genres'])
                            print(f"Género encontrado: {song_info['genre']}")
                    
                    # Obtener información del álbum
                    if 'album' in track and track['album']:
                        if 'name' in track['album']:
                            song_info['album'] = track['album']['name']
                        if 'release_date' in track['album']:
                            song_info['release_date'] = track['album']['release_date']
            except Exception as e:
                print(f"Error al obtener metadatos de Spotify: {e}")
            
            return song_info
            
        except Exception as e:
            print(f"Error general en método alternativo: {e}")
            return {
                'lyrics': "No disponible",
                'genre': "No disponible",
                'album': "No disponible",
                'release_date': "No disponible",
                'writer': "No disponible",
                'producer': "No disponible"
            }


    def getAlbumData(self, album_id):
        """
        Obtiene los datos de un álbum de Spotify.
        
        Args:
            album_id (str): ID del álbum en Spotify
            
        Returns:
            dict: Diccionario con los datos del álbum
        """
        endpoint = f"https://api.spotify.com/v1/albums/{album_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        response = requests.get(endpoint, headers=headers)
        
        # Verificar si la solicitud fue exitosa
        if response.status_code != 200:
            raise Exception(f"Error al obtener datos del álbum: {response.status_code} - {response.text}")
        
        return response.json()
    
    def extract_track_data(self, track):
        """
        Extrae los datos relevantes de una canción de Spotify.
        
        Args:
            track (dict): Datos de la canción obtenidos de la API de Spotify
            
        Returns:
            dict: Diccionario con los datos procesados de la canción
        """
        
        # Extraer datos básicos
        track_data = {
            'id': track['id'],
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'artist_id': track['artists'][0]['id'],
            'album': track['album']['name'],
            'album_id': track['album']['id'],
            'release_date': track['album']['release_date'],
            'popularity': track['popularity'],
            'explicit': track['explicit'],
            'preview_url': track['preview_url'],
            'external_url': track['external_urls']['spotify'],
            
            'uri': track['uri']
        }

        album_data = self.getAlbumData(track_data['album_id'])
        track_data['genres'] = ', '.join(album_data['genres'])
        print(track_data)
        # Extraer imagen del álbum si está disponible
        if track['album']['images'] and len(track['album']['images']) > 0:
            track_data['album_image'] = track['album']['images'][0]['url']
        else:
            track_data['album_image'] = None
        
        return track_data
    
    def enrich_tracks_with_audio_features(self, tracks):
        """
        Enriquece los datos de las canciones con características de audio.
        
        Args:
            tracks (list): Lista de diccionarios con información de las canciones
            
        Returns:
            list: Lista de diccionarios con información enriquecida de las canciones
        """
        enriched_tracks = []
        
        for track in tracks:
            # Obtener características de audio
            audio_features = self.get_audio_features(track['id'])
            
            # Combinar datos
            track_data = track.copy()
            track_data.update(audio_features)
            
            enriched_tracks.append(track_data)
            
            # Esperar un poco para no sobrecargar la API
            time.sleep(1)
        
        return enriched_tracks
    
    def get_artist_genres(self, artist_id):
        """
        Obtiene los géneros de un artista.
        
        Args:
            artist_id (str): ID del artista en Spotify
            
        Returns:
            list: Lista de géneros del artista
        """
        try:
            artist = self.sp.artist(artist_id)
            return artist['genres']
        except Exception as e:
            print(f"Error al obtener géneros del artista: {e}")
            return []
    
    def enrich_tracks_with_genres(self, tracks):
        """
        Enriquece los datos de las canciones con géneros musicales.
        
        Args:
            tracks (list): Lista de diccionarios con información de las canciones
            
        Returns:
            list: Lista de diccionarios con información enriquecida de las canciones
        """
        for track in tracks:
            if 'artist_id' in track:
                genres = self.get_artist_genres(track['artist_id'])
                track['genres'] = genres
            else:
                track['genres'] = []
            
            # Esperar un poco para no sobrecargar la API
            time.sleep(0.5)
        
        return tracks
    
    def estimate_audio_features(self, track_info):
        """
        Estima las características de audio de una canción basándose en metadatos.
        Utiliza el género, popularidad y otros factores para hacer estimaciones razonables.
        
        Args:
            track_info (dict): Información de la canción obtenida de la API de Spotify
            
        Returns:
            dict: Características de audio estimadas
        """
        try:
            # Extraer información básica
            popularity = track_info.get('popularity', 50) / 100.0  # Convertir a escala 0-1
            artist_id = track_info['artists'][0]['id'] if track_info.get('artists') else None
            explicit = track_info.get('explicit', False)
            
            # Obtener géneros del artista
            genres = []
            if artist_id:
                try:
                    artist_info = self.sp.artist(artist_id)
                    genres = artist_info.get('genres', [])
                except Exception as e:
                    print(f"Error al obtener géneros del artista: {e}")
            
            # Analizar géneros para mejorar la estimación
            is_electronic = any(g for g in genres if 'electro' in g.lower() or 'dance' in g.lower() or 'house' in g.lower() or 'techno' in g.lower())
            is_acoustic = any(g for g in genres if 'acoustic' in g.lower() or 'folk' in g.lower() or 'indie' in g.lower())
            is_hiphop = any(g for g in genres if 'hip hop' in g.lower() or 'rap' in g.lower() or 'trap' in g.lower())
            is_rock = any(g for g in genres if 'rock' in g.lower() or 'metal' in g.lower() or 'punk' in g.lower())
            is_classical = any(g for g in genres if 'classical' in g.lower() or 'orchestra' in g.lower() or 'piano' in g.lower())
            
            # Estimar BPM basado en género y popularidad
            base_bpm = 120  # BPM promedio
            if is_electronic:
                base_bpm = 128
            elif is_hiphop:
                base_bpm = 95
            elif is_rock:
                base_bpm = 110
            elif is_classical:
                base_bpm = 85
            
            # Ajustar BPM según popularidad (canciones más populares tienden a ser más rápidas)
            estimated_bpm = base_bpm + (popularity - 0.5) * 20
            
            # Estimar key (tonalidad) basado en popularidad y género
            # Las canciones populares tienden a estar en tonalidades como C, G, D (0, 7, 2)
            popular_keys = [0, 7, 2, 9, 4]  # C, G, D, A, E
            minor_keys = [9, 4, 11, 6, 1]   # Am, Em, Bm, F#m, C#m
            
            if popularity > 0.7:
                # Canciones muy populares suelen estar en tonalidades comunes
                estimated_key = popular_keys[int(popularity * 5) % len(popular_keys)]
            elif is_rock or is_hiphop:
                # Rock y hip hop suelen usar tonalidades menores
                estimated_key = minor_keys[int(popularity * 5) % len(minor_keys)]
            else:
                # Distribución más uniforme para otros géneros
                estimated_key = int(popularity * 12) % 12
            
            # Estimar modo (mayor/menor)
            # Géneros como rock, hip hop tienden a usar modo menor
            # Música pop tiende a usar modo mayor si es muy popular
            if is_rock or is_hiphop:
                estimated_mode = 0  # Menor
            elif popularity > 0.8:
                estimated_mode = 1  # Mayor (canciones muy populares)
            else:
                estimated_mode = 1 if popularity > 0.5 else 0
            
            # Crear características estimadas con mayor precisión
            processed_features = {
                'tempo': estimated_bpm,
                'time_signature': f"4/4",  # La mayoría de canciones populares están en 4/4
                'loudness': -14.0 + popularity * 8,  # Entre -14 y -6 dB (más popular = más fuerte)
                'key': self.get_musical_key(estimated_key),
                'mode': self.get_mode_name(estimated_mode),
                'danceability': 0.3 + popularity * 0.5 + (0.2 if is_electronic else 0),
                'valence': popularity * (1.2 if not is_rock and not is_hiphop else 0.8),  # Ajustar por género
                'energy': min(1.0, popularity * 1.2 + (0.2 if is_electronic or is_rock else 0)),
                'acousticness': min(1.0, max(0.0, 0.8 if is_acoustic else (1.0 - popularity))),
                'instrumentalness': min(1.0, max(0.0, 0.8 if is_classical else 0.1)),
                'liveness': min(1.0, max(0.0, 0.2 + popularity * 0.3 + (0.3 if is_rock else 0))),
                'speechiness': min(1.0, max(0.0, 0.1 + (0.4 if is_hiphop else 0) + (0.1 if explicit else 0))),
                'duration_ms': track_info.get('duration_ms', 180000),  # Valor predeterminado: 3 minutos
                'duration_min': round(track_info.get('duration_ms', 180000) / 60000, 2)
            }
            
            return processed_features
            
        except Exception as e:
            print(f"Error al estimar características de audio: {e}")
            return {
                'danceability': 0.5,
                'energy': 0.5,
                'key': 'C',
                'loudness': -10.0,
                'mode': 'Mayor',
                'speechiness': 0.1,
                'acousticness': 0.3,
                'instrumentalness': 0.1,
                'liveness': 0.2,
                'valence': 0.5,
                'tempo': 120,
                'time_signature': '4/4',
                'duration_ms': 180000,
                'duration_min': 3.0
            }
    
    def enrich_tracks_with_lyrics(self, tracks):
        """
        Enriquece los datos de las canciones con letras.
        
        Args:
            tracks (list): Lista de diccionarios con información de las canciones
            
        Returns:
            list: Lista de diccionarios con información enriquecida de las canciones
        """
        for track in tracks:
            if 'id' in track:
                # Intentar obtener letra de la API de Spotify
                lyrics = self.get_lyrics_from_spotify_api(track['id'])
                
                # Si no se pudo obtener, intentar con web scraping
                if not lyrics or "error" in lyrics.lower():
                    lyrics = self.search_song_lyrics(track['name'], track['artist'])
                
                track['lyrics'] = lyrics
            else:
                track['lyrics'] = "No disponible"
            
            # Esperar un poco para no sobrecargar la API
            time.sleep(1)
        
        return tracks
    
    def check_ffmpeg(self):
        """
        Verifica si FFmpeg está instalado.
        
        Returns:
            bool: True si FFmpeg está instalado, False en caso contrario
        """
        try:
            import shutil
            return shutil.which('ffmpeg') is not None
        except Exception:
            return False
    
    def convert_to_wav(self, input_file, output_file=None):
        """
        Convierte un archivo de audio a formato WAV.
        
        Args:
            input_file (str): Ruta del archivo de entrada
            output_file (str, optional): Ruta del archivo de salida
            
        Returns:
            str: Ruta del archivo convertido o None si falló la conversión
        """
        try:
            if output_file is None:
                output_file = os.path.splitext(input_file)[0] + ".wav"
            
            # Intentar usar FFmpeg si está disponible
            if self.check_ffmpeg():
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
    
    def analyze_audio_file(self, audio_file_path):
        """
        Analiza un archivo de audio con librosa.
        
        Args:
            audio_file_path (str): Ruta del archivo de audio
            track_info (dict, optional): Información de la pista
            
        Returns:
            dict: Características de audio extraídas del archivo
        """
        try:
            print(f"Analizando archivo de audio: {audio_file_path}")
            
            # Verificar si el archivo existe
            if not os.path.exists(audio_file_path):
                print(f"El archivo {audio_file_path} no existe")
                return None
            
            # Intentar convertir a WAV si no es un archivo .wav o .mp3
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            temp_wav = None
            
            if file_ext not in [".wav", ".mp3"]:
                print(f"Formato {file_ext} puede no ser compatible con librosa. Intentando convertir...")
                wav_path = self.convert_to_wav(audio_file_path)
                if wav_path:
                    temp_wav = wav_path
                    audio_file_path = wav_path
                    print(f"Convertido exitosamente a {wav_path}")
                else:
                    print("No se pudo convertir el archivo. Intentando procesar el original...")
            
            # Cargar y analizar el audio con librosa
            try:
                # Intentar cargar con diferentes configuraciones
                try:
                    y, sr = librosa.load(audio_file_path, sr=None)
                except:
                    try:
                        y, sr = librosa.load(audio_file_path, sr=22050)
                    except:
                        print("No se pudo cargar el audio con librosa. Intentando con configuración mínima...")
                        y, sr = librosa.load(audio_file_path, sr=22050, mono=True, duration=30)
                
                # Extraer características
                # Tempo (BPM)
                onset_env = librosa.onset.onset_strength(y=y, sr=sr)
                tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
                
                # Características espectrales
                spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0])
                spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)[0])
                spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)[0])
                
                # Características de timbre (MFCC)
                mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
                mfcc_mean = np.mean(mfcc, axis=1)
                
                # Características rítmicas
                y_harmonic, y_percussive = librosa.effects.hpss(y)
                tempo_harmonic, _ = librosa.beat.beat_track(y=y_harmonic, sr=sr)
                tempo_percussive, _ = librosa.beat.beat_track(y=y_percussive, sr=sr)
                
                # Características de armonía
                chroma = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr)
                chroma_mean = np.mean(chroma, axis=1)
                
                # Crear diccionario de resultados
                results = {
                    'tempo_librosa': tempo,
                    'tempo_harmonic': tempo_harmonic,
                    'tempo_percussive': tempo_percussive,
                    'spectral_centroid': spectral_centroid,
                    'spectral_bandwidth': spectral_bandwidth,
                    'spectral_rolloff': spectral_rolloff,
                    'mfcc_mean': mfcc_mean.tolist(),
                    'chroma_mean': chroma_mean.tolist()
                }
                
                # Limpiar archivos temporales
                if temp_wav and os.path.exists(temp_wav):
                    os.remove(temp_wav)
                
                return results
                
            except Exception as e:
                print(f"Error al analizar audio con librosa: {e}")
                
                # Limpiar archivos temporales
                if temp_wav and os.path.exists(temp_wav):
                    os.remove(temp_wav)
                
                return None
                
        except Exception as e:
            print(f"Error general al analizar archivo de audio: {e}")
            return None
    
    def get_tracks_from_playlists(self, playlist_ids, num_songs=20):
        """
        Obtiene canciones de varias playlists de Spotify.
        
        Args:
            playlist_ids (list): Lista de IDs de playlists de Spotify
            num_songs (int, optional): Número máximo de canciones a obtener
            
        Returns:
            list: Lista de diccionarios con información de las canciones
        """
        all_tracks = []
        final_tracks = []
        try:
            track_ids_set = set()  # Para evitar duplicados
            
            for playlist_id in playlist_ids:
                tracks_res = self.get_playlist_tracks(playlist_id)
                for item in tracks_res['items']:
                    if item['track'] and item['track']['id'] and item['track']['id'] not in track_ids_set:
                        track_ids_set.add(item['track']['id'])
                        all_tracks.append(item['track'])
        
            print(f"Se obtuvieron {len(all_tracks)} canciones de las playlists.")
        
            # Limitar al número de canciones especificado
            # Invierte la lista de canciones y limita al número especificado
            limited_tracks = all_tracks[::-1][:num_songs]
            
        
            # Procesar y enriquecer las canciones
            processed_tracks = []
            for track in limited_tracks:
                try:
                    print(f"Procesando canción: {track.get('name', 'Desconocida')} - {track.get('artists', [{}])[0].get('name', 'Desconocido')}")
                    track_data = self.extract_track_data(track)
                    
                    # Obtener características de audio
                    try:
                        audio_features = self.get_audio_features_from_youtube(track_data)
                    except Exception as e:
                        print(f"Error al obtener características de audio: {e}")
                        audio_features = {}
                    
                    # Obtener letras
                    try:
                        track_lyrics = self.get_song_lyrics_from_genius(track_data['name'], track_data['artist'])
                        track_data['lyrics'] = track_lyrics.get('lyrics', 'No disponible')
                    except Exception as e:
                        print(f"Error al obtener letras: {e}")
                        track_data['lyrics'] = "No disponible"
                    
                    # Obtener géneros
                    try:
                        genres = self.get_artist_genres(track_data['artist_id'])
                        track_data.update(genres)
                    except Exception as e:
                        print(f"Error al obtener géneros: {e}")
                        track_data['genres'] = "No disponible"
                    
                    # Actualizar datos y añadir a las listas
                    track_data.update(audio_features)
                    processed_tracks.append(track_data)
                    final_tracks.append(track_data)
                    print(f"Canción procesada con éxito: {track_data['name']}")
                    
                except Exception as e:
                    print(f"Error al procesar canción {track.get('name', 'Desconocida')}: {e}")
                    # Continuar con la siguiente canción
        
            return final_tracks
        except Exception as e:
            print(f"Error al obtener canciones de las playlists: {e}, solo se pudieron guardar {len(final_tracks)} canciones")
            return final_tracks
        
    def get_artist_genres(self, artist_id):
        """
        Obtiene los géneros de un artista de Spotify.
        
        Args:
            artist_id (str): ID del artista de Spotify
            
        Returns:
            list: Lista de géneros del artista
        """
        artist = self.sp.artist(artist_id)
        return {"genres": ', '.join(artist['genres'])}

    def get_audio_features_from_youtube(self, track, access_token=None):
        """
        Obtiene las características de audio de una canción específica de Spotify.
        Utiliza Librosa para extraer directamente las características de audio del archivo de preview.
        
        Args:
            track_id (str): ID de la canción de Spotify
            access_token (str, optional): Token de acceso a la API de Spotify. Si no se proporciona,
                                        se utilizará la instancia global de spotipy.
            
        Returns:
            dict: Características de audio de la canción
        """
        try:
            # Buscar la canción en YouTube usando yt-dlp

            artist_name = track['artist']
            track_id = track['id']
            track_name = track['name']
            search_query = f"{artist_name} - {track_name} official audio"
            print(f"Buscando en YouTube: {search_query}")
                        
            # Crear directorio temporal para descargas
            temp_dir = "temp_audio"
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, f"temp_{track_id}.mp3")
                        
            # Eliminar archivo temporal si ya existe
            if os.path.exists(temp_file):
                os.remove(temp_file)
                        
            # Verificar si FFmpeg está instalado
            has_ffmpeg = self.check_ffmpeg()
                        
            # Configurar opciones de yt-dlp
            if has_ffmpeg:
                print("FFmpeg está instalado. Descargando y convirtiendo a MP3...")
                # Con FFmpeg podemos convertir a MP3
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(temp_dir, f'temp_{track_id}.%(ext)s'),
                    'noplaylist': True,
                    'quiet': False,  # Mostrar más información para depuración
                    'no_warnings': False,  # Mostrar advertencias
                    'default_search': 'ytsearch',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            else:
                # Sin FFmpeg, descargar el audio en su formato original
                print("FFmpeg no está instalado. Descargando en formato original...")
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(temp_dir, f'temp_{track_id}.%(ext)s'),
                    'noplaylist': True,
                    'quiet': False,  # Mostrar más información para depuración
                    'no_warnings': False,  # Mostrar advertencias
                    'default_search': 'ytsearch',
                    # Sin postprocesadores que requieran FFmpeg
                }
                        
            # Buscar y descargar usando yt-dlp
            print(f"Descargando audio de YouTube...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Buscar el video
                info = ydl.extract_info(f"ytsearch1:{search_query}", download=True)
                entries = info.get('entries', [])
                            
                if entries:
                    # Obtener información del primer resultado
                    entry = entries[0]
                    video_title = entry.get('title', 'Unknown')
                    print(f"Encontrado en YouTube: {video_title}")
                                
                    # Buscar el archivo descargado (puede tener cualquier extensión)
                    # Primero intentamos con .mp3, luego buscamos cualquier archivo con el prefijo correcto
                    output_file = os.path.join(temp_dir, f"temp_{track_id}.mp3")
                                
                    if not os.path.exists(output_file):
                        # Buscar cualquier archivo con el prefijo correcto
                        for file in os.listdir(temp_dir):
                            if file.startswith(f"temp_{track_id}."):
                                output_file = os.path.join(temp_dir, file)
                                print(f"Encontrado archivo: {output_file}")
                                break
                                            
                    # Si encontramos un archivo que no es MP3 y tenemos FFmpeg, convertirlo
                    if os.path.exists(output_file) and not output_file.endswith('.mp3') and has_ffmpeg:
                        try:
                            mp3_file = os.path.splitext(output_file)[0] + ".mp3"
                            print(f"Convirtiendo {output_file} a {mp3_file} usando FFmpeg...")
                            import subprocess
                            result = subprocess.run(["ffmpeg", "-i", output_file, "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", mp3_file],
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            if os.path.exists(mp3_file):
                                print(f"Conversión exitosa a {mp3_file}")
                                # Eliminar el archivo original
                                os.remove(output_file)
                                output_file = mp3_file
                        except Exception as e:
                            print(f"Error al convertir a MP3 con FFmpeg: {e}")
                    
                    if os.path.exists(output_file):
                        print(f"Audio descargado: {output_file}")
                        # Analizar el audio descargado con librosa
                        return self.analyze_audio_file(output_file, track)
                    else:
                        print(f"No se pudo encontrar el archivo descargado")
                else:
                    print("No se encontraron resultados en YouTube")
        except Exception as e:
            print(f"Excepción al obtener características de audio: {e}")
            return {}

    def analyze_audio_file(self, audio_file_path, track_info=None):
        try:
            print(f"Analizando archivo de audio: {audio_file_path}")
            
            # Verificar si el archivo existe
            if not os.path.exists(audio_file_path):
                print(f"El archivo {audio_file_path} no existe")
                return None
            
            # Intentar convertir a WAV si no es un archivo .wav o .mp3
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            temp_wav = None
            
            if file_ext not in [".wav", ".mp3"]:
                print(f"Formato {file_ext} puede no ser compatible con librosa. Intentando convertir...")
                wav_path = convert_to_wav(audio_file_path)
                if wav_path:
                    temp_wav = wav_path
                    audio_file_path = wav_path
                    print(f"Convertido exitosamente a {wav_path}")
                else:
                    print("No se pudo convertir el archivo. Intentando procesar el original...")
            
            # Cargar y analizar el audio con librosa
            try:
                # Intentar cargar con diferentes configuraciones
                try:
                    y, sr = librosa.load(audio_file_path, sr=None, mono=True)
                except:
                    print("Intentando con tasa de muestreo fija...")
                    y, sr = librosa.load(audio_file_path, sr=22050, mono=True)
            except Exception as e:
                print(f"Error al cargar el audio: {e}")
                return None
            
            print(f"Audio cargado correctamente: {len(y)} muestras, {sr}Hz")
            
            # Extraer características
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr).mean()
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr).mean()
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y).mean()
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfccs_mean = mfccs.mean(axis=1)
            
            # Análisis de croma para detección de tonalidad musical
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            key_idx = np.argmax(chroma_mean)
            
            # Detección de modo (mayor/menor) usando características espectrales
            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
            contrast_mean = np.mean(spectral_contrast, axis=1)
            mode = 1 if contrast_mean[1] > 0 else 0  # Mayor si el segundo componente es positivo
            
            # Calcular energía y otras características
            rms = librosa.feature.rms(y=y)[0]
            energy = np.mean(rms)
            
            # Cálculo de danceability basado en la regularidad de los beats
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr)
            danceability = np.mean(pulse)
            
            # Extraer más características para mejorar la precisión
            spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
            spectral_flatness = np.mean(librosa.feature.spectral_flatness(y=y))
            
            # Mapear las características a un formato similar al de Spotify
            processed_features = {
                'bpm': float(tempo),
                'signature': 4,  # Asumimos 4/4 como valor por defecto
                'loudness': -20.0 * np.log10(np.maximum(1e-10, energy)),  # Convertir a dB
                'key': int(key_idx),  # 0=C, 1=C#, 2=D, etc.
                'mode': mode,  # 0 = menor, 1 = mayor
                'danceability': min(1.0, max(0.0, danceability)),
                'valence': min(1.0, max(0.0, 0.5 + (spectral_contrast[0].mean() / 50))),  # Aproximación de valence
                'energy': min(1.0, max(0.0, energy * 10)),
                'acousticness': min(1.0, max(0.0, 1.0 - spectral_flatness)),
                'instrumentalness': min(1.0, max(0.0, spectral_flatness * 2)),
                'liveness': min(1.0, max(0.0, zero_crossing_rate)),
                'speechiness': min(1.0, max(0.0, mfccs_mean[1] / 100))
            }
            
            print(f"Características de audio analizadas con librosa")
            return processed_features
            
        except Exception as e:
            print(f"Error en el análisis de audio con librosa: {e}")
            return None
        finally:
            # Limpiar archivos temporales
            try:
                # No eliminar archivos de YouTube, solo los temporales de conversión
                if temp_wav and os.path.exists(temp_wav) and not temp_wav.startswith(os.path.join("temp_audio")):
                    os.remove(temp_wav)
                    print(f"Archivo temporal WAV eliminado: {temp_wav}")
                
                # Eliminar archivos temporales que no sean de YouTube
                if not audio_file_path.startswith(os.path.join("temp_audio")) and os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                    print(f"Archivo temporal eliminado: {audio_file_path}")
            except Exception as e:
                print(f"Error al eliminar archivos temporales: {e}")