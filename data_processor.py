#!/usr/bin/env python3
"""
Módulo para procesamiento de datos en DataFrames.
Proporciona funciones para cargar, limpiar y manipular datos de canciones de Spotify.
"""

import pandas as pd
import numpy as np
import re
import os
from typing import List, Dict, Any, Optional, Union


class DataProcessor:
    """
    Clase para procesar y limpiar datos de canciones de Spotify.
    Proporciona métodos para cargar datos desde Excel, limpiar valores,
    eliminar duplicados y normalizar formatos.
    """
    
    def __init__(self):
        """Inicializa el procesador de datos."""
        self.column_translations = {
            'id': 'ID',
            'name': 'Nombre',
            'artist': 'Artista',
            'album': 'Álbum',
            'release_date': 'Fecha de lanzamiento',
            'popularity': 'Popularidad',
            'explicit': 'Explícito',
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
            'duration_min': 'Duración (min)',
            'genres': 'Géneros',
            'lyrics': 'Letra',
            'artist_id': 'ID del artista',
            'album_id': 'ID del álbum',
            'preview_url': 'URL de preview',
            'external_url': 'URL de Spotify',
            'uri': 'URI de Spotify',
            'album_image': 'Imagen del álbum'
        }
        
        # Orden preferido de columnas para una mejor presentación
        self.columns_order = [
            'name', 'artist', 'album', 'release_date', 'popularity', 'explicit',
            'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness',
            'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo',
            'time_signature', 'duration_ms', 'duration_min', 'genres', 'id',
            'artist_id', 'album_id', 'preview_url', 'external_url', 'uri', 
            'album_image', 'lyrics'
        ]
    
    def load_from_excel(self, file_path: str) -> pd.DataFrame:
        """
        Carga datos desde un archivo Excel.
        
        Args:
            file_path (str): Ruta al archivo Excel
            
        Returns:
            pd.DataFrame: DataFrame con los datos cargados
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo no es un Excel válido
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"El archivo {file_path} no existe")
            
            print(f"Cargando datos desde {file_path}...")
            df = pd.read_excel(file_path)
            print(f"Datos cargados: {len(df)} filas, {len(df.columns)} columnas")
            
            # Verificar si las columnas están en español o inglés
            if 'Nombre' in df.columns:
                # Invertir el diccionario de traducciones para convertir de español a inglés
                reverse_translations = {v: k for k, v in self.column_translations.items()}
                df = df.rename(columns=reverse_translations)
                print("Columnas convertidas de español a inglés")
            
            return df
            
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                raise
            else:
                raise ValueError(f"Error al cargar el archivo Excel: {e}")
    
    def remove_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Elimina filas duplicadas del DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame a procesar
            subset (List[str], optional): Columnas a considerar para identificar duplicados.
                                         Si es None, se usa ['id'] o ['name', 'artist'] si 'id' no existe.
        
        Returns:
            pd.DataFrame: DataFrame sin duplicados
        """
        if subset is None:
            if 'id' in df.columns:
                subset = ['id']
            else:
                subset = ['name', 'artist']
        
        original_count = len(df)
        df = df.drop_duplicates(subset=subset, keep='first')
        removed_count = original_count - len(df)
        
        print(f"Duplicados eliminados: {removed_count} filas (basado en {subset})")
        return df
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y normaliza los datos del DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame a limpiar
            
        Returns:
            pd.DataFrame: DataFrame limpio
        """
        # Hacer una copia para no modificar el original
        df_clean = df.copy()
        
        # Eliminar filas completamente vacías
        df_clean = df_clean.dropna(how='all')
        
        # Limpiar valores de texto
        for col in df_clean.select_dtypes(include=['object']).columns:
            if col in ['lyrics', 'genres']:
                continue  # No limpiar letras ni géneros
            
            # Reemplazar valores nulos con cadena vacía y limpiar espacios
            df_clean[col] = df_clean[col].fillna('').astype(str).str.strip()
        
        # Convertir columnas numéricas
        numeric_cols = ['popularity', 'danceability', 'energy', 'loudness', 
                        'speechiness', 'acousticness', 'instrumentalness', 
                        'liveness', 'valence', 'tempo', 'duration_ms']
        
        for col in numeric_cols:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Calcular duración en minutos si no existe
        if 'duration_ms' in df_clean.columns and 'duration_min' not in df_clean.columns:
            df_clean['duration_min'] = df_clean['duration_ms'] / 60000
            df_clean['duration_min'] = df_clean['duration_min'].round(2)
        
        # Normalizar fechas
        if 'release_date' in df_clean.columns:
            df_clean['release_date'] = pd.to_datetime(df_clean['release_date'], errors='coerce')
        
        # Convertir booleanos
        if 'explicit' in df_clean.columns:
            df_clean['explicit'] = df_clean['explicit'].map({
                True: True, 'True': True, 'true': True, 1: True, '1': True, 'Yes': True, 'yes': True,
                False: False, 'False': False, 'false': False, 0: False, '0': False, 'No': False, 'no': False,
            })
        
        print(f"DataFrame limpiado: {len(df_clean)} filas")
        return df_clean
    
    def normalize_text_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza las columnas de texto, eliminando caracteres especiales y normalizando acentos.
        
        Args:
            df (pd.DataFrame): DataFrame a normalizar
            
        Returns:
            pd.DataFrame: DataFrame con texto normalizado
        """
        import unicodedata
        
        df_norm = df.copy()
        
        # Función para normalizar texto
        def normalize_text(text):
            if not isinstance(text, str):
                return text
            
            # Normalizar caracteres Unicode (NFD) y eliminar diacríticos
            text = unicodedata.normalize('NFKD', text)
            # Volver a normalizar a NFC para tener una representación consistente
            text = unicodedata.normalize('NFC', text)
            return text
        
        # Aplicar normalización a columnas de texto excepto letras
        for col in df_norm.select_dtypes(include=['object']).columns:
            if col != 'lyrics':
                df_norm[col] = df_norm[col].apply(normalize_text)
        
        return df_norm
    
    def merge_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                         on: Optional[List[str]] = None, 
                         how: str = 'outer') -> pd.DataFrame:
        """
        Combina dos DataFrames, manteniendo la información más completa.
        
        Args:
            df1 (pd.DataFrame): Primer DataFrame
            df2 (pd.DataFrame): Segundo DataFrame
            on (List[str], optional): Columnas para hacer el merge. 
                                     Si es None, se usa 'id' o ['name', 'artist']
            how (str): Tipo de merge ('outer', 'inner', 'left', 'right')
            
        Returns:
            pd.DataFrame: DataFrame combinado
        """
        if on is None:
            if 'id' in df1.columns and 'id' in df2.columns:
                on = 'id'
            else:
                on = ['name', 'artist']
        
        # Realizar el merge
        merged_df = pd.merge(df1, df2, on=on, how=how, suffixes=('_1', '_2'))
        
        # Combinar columnas con sufijos
        for col in df1.columns:
            if f"{col}_1" in merged_df.columns and f"{col}_2" in merged_df.columns:
                # Preferir valores no nulos
                merged_df[col] = merged_df[f"{col}_1"].combine_first(merged_df[f"{col}_2"])
                # Eliminar columnas duplicadas
                merged_df = merged_df.drop([f"{col}_1", f"{col}_2"], axis=1)
        
        print(f"DataFrames combinados: {len(merged_df)} filas")
        return merged_df
    
    def format_for_excel(self, df: pd.DataFrame, translate_columns: bool = True) -> pd.DataFrame:
        """
        Formatea el DataFrame para exportar a Excel, reordenando columnas y traduciendo nombres.
        
        Args:
            df (pd.DataFrame): DataFrame a formatear
            translate_columns (bool): Si se deben traducir los nombres de columnas al español
            
        Returns:
            pd.DataFrame: DataFrame formateado
        """
        # Hacer una copia para no modificar el original
        df_formatted = df.copy()
        
        # Reordenar columnas (solo las que existen en el DataFrame)
        existing_columns = [col for col in self.columns_order if col in df_formatted.columns]
        
        # Añadir columnas que no estén en el orden predefinido
        for col in df_formatted.columns:
            if col not in existing_columns:
                existing_columns.append(col)
        
        df_formatted = df_formatted[existing_columns]
        
        # Traducir nombres de columnas si se solicita
        if translate_columns:
            translations = {k: v for k, v in self.column_translations.items() 
                           if k in df_formatted.columns}
            df_formatted = df_formatted.rename(columns=translations)
        
        return df_formatted
    
    def save_to_excel(self, df: pd.DataFrame, file_path: str, 
                     translate_columns: bool = True, 
                     index: bool = False) -> None:
        """
        Guarda el DataFrame en un archivo Excel.
        
        Args:
            df (pd.DataFrame): DataFrame a guardar
            file_path (str): Ruta donde guardar el archivo
            translate_columns (bool): Si se deben traducir los nombres de columnas al español
            index (bool): Si se debe incluir el índice en el Excel
            
        Returns:
            None
        """
        # Formatear para Excel
        df_to_save = self.format_for_excel(df, translate_columns)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Guardar a Excel
        try:
            df_to_save.to_excel(file_path, index=index)
            print(f"DataFrame guardado exitosamente en {file_path}")
            print(f"Dimensiones: {len(df_to_save)} filas, {len(df_to_save.columns)} columnas")
        except Exception as e:
            print(f"Error al guardar el archivo Excel: {e}")
    
    def filter_by_criteria(self, df: pd.DataFrame, criteria: Dict[str, Any]) -> pd.DataFrame:
        """
        Filtra el DataFrame según criterios específicos.
        
        Args:
            df (pd.DataFrame): DataFrame a filtrar
            criteria (Dict[str, Any]): Diccionario con criterios de filtrado
                                      {columna: valor} o {columna: (operador, valor)}
                                      Operadores: '>', '<', '>=', '<=', '==', '!=', 'contains'
            
        Returns:
            pd.DataFrame: DataFrame filtrado
        """
        df_filtered = df.copy()
        
        for column, condition in criteria.items():
            if column not in df_filtered.columns:
                print(f"Advertencia: Columna '{column}' no existe en el DataFrame")
                continue
            
            if isinstance(condition, tuple) and len(condition) == 2:
                operator, value = condition
                
                if operator == '>':
                    df_filtered = df_filtered[df_filtered[column] > value]
                elif operator == '<':
                    df_filtered = df_filtered[df_filtered[column] < value]
                elif operator == '>=':
                    df_filtered = df_filtered[df_filtered[column] >= value]
                elif operator == '<=':
                    df_filtered = df_filtered[df_filtered[column] <= value]
                elif operator == '==':
                    df_filtered = df_filtered[df_filtered[column] == value]
                elif operator == '!=':
                    df_filtered = df_filtered[df_filtered[column] != value]
                elif operator == 'contains':
                    if df_filtered[column].dtype == 'object':
                        df_filtered = df_filtered[df_filtered[column].str.contains(value, na=False)]
                    else:
                        print(f"Advertencia: Operador 'contains' no aplicable a columna {column}")
            else:
                # Si es un valor simple, aplicar igualdad
                df_filtered = df_filtered[df_filtered[column] == condition]
        
        print(f"DataFrame filtrado: {len(df_filtered)} de {len(df)} filas")
        return df_filtered


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia del procesador
    processor = DataProcessor()
    
    # Ejemplo: cargar datos, limpiar y guardar
    try:
        # Cargar datos (cambiar por una ruta real)
        file_path = "spotify_songs.xlsx"
        if os.path.exists(file_path):
            df = processor.load_from_excel(file_path)
            
            # Limpiar datos
            df_clean = processor.clean_dataframe(df)
            
            # Eliminar duplicados
            df_unique = processor.remove_duplicates(df_clean)
            
            # Guardar resultado
            output_path = "spotify_songs_cleaned.xlsx"
            processor.save_to_excel(df_unique, output_path)
            
            print(f"Proceso completado. Archivo guardado en {output_path}")
        else:
            print(f"El archivo {file_path} no existe. Ejecute primero el script principal para generar datos.")
    except Exception as e:
        print(f"Error en el procesamiento: {e}")
