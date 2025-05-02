# Spotify Excel Generator

Este proyecto genera un archivo Excel con datos de canciones de Spotify, incluyendo:
- ID de Spotify
- Nombre de la canción
- Artista
- Año de lanzamiento
- Popularidad
- Duración
- Características de audio (BPM, Tonalidad, Modo, etc.)
- Géneros musicales
- Letras de canciones
- Y más...

## Características Principales

- **Generación de Excel**: Crea un archivo Excel con datos detallados de canciones de Spotify.
- **Personalización de cantidad**: Permite especificar cuántas canciones incluir en el Excel.
- **Completar datos faltantes**: Función para completar características de audio faltantes en archivos Excel existentes.
- **Extracción de múltiples playlists**: Obtiene canciones de varias playlists de Spotify.
- **Deduplicación**: Evita canciones duplicadas en el resultado final.
- **Datos enriquecidos**: Incluye características de audio, géneros y letras de canciones.

## Requisitos

- Python 3.8+
- Cuenta de Spotify Developer
- Dependencias (ver `requirements.txt`)

## Configuración

1. Crea una aplicación en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Obtén tu Client ID y Client Secret
3. Crea un archivo `.env` en la raíz del proyecto con:
   ```
   SPOTIFY_CLIENT_ID=tu_client_id
   SPOTIFY_CLIENT_SECRET=tu_client_secret
   ```
4. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

## Uso

### Generar un nuevo archivo Excel

Para generar un archivo Excel con el número predeterminado de canciones (20):
```
python spotify_excel_generator.py
```

Para especificar el número de canciones a incluir (por ejemplo, 100):
```
python spotify_excel_generator.py 100
```

### Completar datos faltantes en un archivo Excel existente

Para completar características de audio faltantes en el archivo Excel predeterminado (`spotify_songs.xlsx`):
```
python spotify_excel_generator.py completar
```

Para completar características de audio en un archivo Excel específico:
```
python spotify_excel_generator.py completar mi_archivo.xlsx
```

## Datos incluidos en el Excel

El archivo Excel generado incluye las siguientes columnas:
- **ID**: Identificador único de la canción en Spotify
- **Nombre**: Título de la canción
- **Artista**: Nombre del artista o artistas
- **Año**: Año de lanzamiento
- **Popularidad**: Índice de popularidad en Spotify (0-100)
- **Duración**: Duración de la canción en formato mm:ss
- **BPM**: Beats por minuto (tempo)
- **Compás**: Signatura de tiempo (ej. 4/4)
- **Volumen**: Volumen general de la pista (loudness)
- **Tonalidad**: Tonalidad musical (C, C#, D, etc.)
- **Modo**: Modo musical (Mayor o Menor)
- **Bailabilidad**: Qué tan adecuada es la canción para bailar (0.0-1.0)
- **Valencia**: Positividad musical de la canción (0.0-1.0)
- **Energía**: Intensidad y actividad percibida (0.0-1.0)
- **Acústico**: Probabilidad de que la canción sea acústica (0.0-1.0)
- **Instrumental**: Probabilidad de que la canción no tenga vocales (0.0-1.0)
- **En vivo**: Probabilidad de que la canción sea una grabación en vivo (0.0-1.0)
- **Hablado**: Presencia de palabras habladas (0.0-1.0)
- **Género**: Géneros musicales asociados
- **Letra**: Letra de la canción (si está disponible)
- **Álbum**: Nombre del álbum

## Notas

- La API de Spotify tiene límites de tasa. Si recibes errores 429, espera unos minutos antes de volver a intentarlo.
- Algunas características pueden no estar disponibles para todas las canciones.
- La función de completar datos crea un nuevo archivo con el sufijo "_completado" para preservar el original.

## Solución de problemas

Si encuentras errores relacionados con la API, verifica:
1. Que tus credenciales de Spotify sean correctas en el archivo `.env`
2. Que no hayas excedido los límites de tasa de la API
3. Que tengas una conexión a internet estable

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir los cambios propuestos.
