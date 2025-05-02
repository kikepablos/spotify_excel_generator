#!/usr/bin/env python3
"""
Módulo para crear y gestionar archivos Excel con datos de Spotify
"""

import os
import time
import pandas as pd
import numpy as np

class ExcelManager:
    def __init__(self):
        """
        Inicializa la clase ExcelManager para gestionar archivos Excel.
        """
        pass
    
    def create_excel(self, tracks, output_file='spotify_songs.xlsx'):
        """
        Crea un archivo Excel con los datos de las canciones.
        
        Args:
            tracks (list): Lista de diccionarios con información de las canciones
            output_file (str): Nombre del archivo Excel a crear
        """
        # Crear DataFrame con los datos
        df = pd.DataFrame(tracks)
        
        # # Reordenar columnas para una mejor presentación
        # columns_order = [
        #     'name', 'artist', 'album', 'release_date', 'popularity', 'explicit',
        #     'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness',
        #     'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo',
        #     'time_signature', 'duration_ms', 'duration_min', 'genres', 'lyrics'
        # ]
        
        
        # # Reordenar columnas (solo las que existen en el DataFrame)
        # existing_columns = [col for col in columns_order if col in df.columns]
        # df = df[existing_columns]
        
        # # Traducir nombres de columnas
        # column_translations = {
        #     'id': 'ID',
        #     'name': 'Nombre',
        #     'artist': 'Artista',
        #     'album': 'Álbum',
        #     'release_date': 'Fecha de lanzamiento',
        #     'popularity': 'Popularidad',
        #     'explicit': 'Explícito',
        #     'danceability': 'Bailabilidad',
        #     'energy': 'Energía',
        #     'key': 'Tonalidad',
        #     'loudness': 'Volumen (dB)',
        #     'mode': 'Modo',
        #     'speechiness': 'Hablado',
        #     'acousticness': 'Acústica',
        #     'instrumentalness': 'Instrumental',
        #     'liveness': 'En vivo',
        #     'valence': 'Valencia',
        #     'tempo': 'Tempo (BPM)',
        #     'time_signature': 'Compás',
        #     'duration_ms': 'Duración (ms)',
        #     'duration_min': 'Duración (min)',
        #     'genres': 'Géneros',
        #     'lyrics': 'Letra',
        # }
        
        # df = df.rename(columns=column_translations)
        
        # Guardar DataFrame en Excel
        try:
            df.to_excel(output_file, index=False)
            print(f"Archivo Excel creado exitosamente: {output_file}")
            return True
        except Exception as e:
            print(f"Error al crear archivo Excel: {e}")
            return False
    
    def complete_excel_audio_features(self, excel_file='spotify_songs.xlsx'):
        """
        Completa un archivo Excel existente con características de audio de Spotify.
        
        Args:
            excel_file (str): Ruta del archivo Excel a completar
            
        Returns:
            bool: True si se completó exitosamente, False en caso contrario
        """
        try:
            # Verificar si el archivo existe
            if not os.path.exists(excel_file):
                print(f"El archivo {excel_file} no existe.")
                return False
            
            # Cargar el archivo Excel
            df = pd.read_excel(excel_file)
            
            # Verificar si hay columnas de ID de Spotify
            if 'ID' not in df.columns and 'id' not in df.columns:
                print("El archivo Excel no contiene una columna con IDs de Spotify.")
                return False
            
            # Determinar el nombre de la columna de ID
            id_column = 'ID' if 'ID' in df.columns else 'id'
            
            # Mapeo de nombres en español a nombres de la API
            api_to_spanish = {
                'danceability': 'Bailabilidad',
                'energy': 'Energía',
                'key': 'Tonalidad',
                'loudness': 'Volumen (dB)',
                'mode': 'Modo',
                'speechiness': 'Hablado',
                'acousticness': 'Acústica',
                'instrumentalness': 'Instrumental',
                'liveness': 'En vivo',
                'valence': 'Valencia',
                'tempo': 'Tempo (BPM)',
                'time_signature': 'Compás',
                'duration_ms': 'Duración (ms)',
                'duration_min': 'Duración (min)'
            }
            
            # Crear columnas faltantes
            for api_name, spanish_name in api_to_spanish.items():
                if spanish_name not in df.columns:
                    df[spanish_name] = None
            
            return df, api_to_spanish, id_column
            
        except Exception as e:
            print(f"Error al procesar archivo Excel: {e}")
            return False
    
    def update_excel_with_audio_features(self, df, track_id, audio_features, api_to_spanish, index):
        """
        Actualiza un DataFrame con características de audio de una canción.
        
        Args:
            df (pandas.DataFrame): DataFrame a actualizar
            track_id (str): ID de la canción
            audio_features (dict): Características de audio de la canción
            api_to_spanish (dict): Mapeo de nombres de API a nombres en español
            index (int): Índice de la fila a actualizar
            
        Returns:
            bool: True si se actualizó exitosamente, False en caso contrario
        """
        try:
            updated = False
            
            # Actualizar cada característica de audio
            for api_name, spanish_name in api_to_spanish.items():
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
            
            return updated
            
        except Exception as e:
            print(f"Error al actualizar DataFrame: {e}")
            return False
    
    def save_updated_excel(self, df, excel_file, updated_rows):
        """
        Guarda un DataFrame actualizado en un archivo Excel.
        
        Args:
            df (pandas.DataFrame): DataFrame a guardar
            excel_file (str): Nombre del archivo Excel original
            updated_rows (int): Número de filas actualizadas
            
        Returns:
            bool: True si se guardó exitosamente, False en caso contrario
        """
        try:
            if updated_rows > 0:
                output_file = excel_file.replace('.xlsx', '_completado.xlsx')
                df.to_excel(output_file, index=False)
                print(f"Se actualizaron {updated_rows} canciones con datos de audio features.")
                print(f"Archivo Excel actualizado guardado como: {output_file}")
                return True
            else:
                print("No se encontraron filas para actualizar.")
                return False
                
        except Exception as e:
            print(f"Error al guardar archivo Excel: {e}")
            return False
