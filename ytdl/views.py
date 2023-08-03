from django.shortcuts import render
from django.http import HttpResponse
from .forms import DownloadForm
import youtube_dl
import re
import concurrent.futures

def extract_video_info(video_url):
    ydl_opts = {}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(video_url, download=False)

def download_video(request):
    form = DownloadForm(request.POST or None)
    
    if form.is_valid():
        video_url = form.cleaned_data.get("url")
        regex = r'^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+'
        if not re.match(regex, video_url):
            return HttpResponse('Enter correct URL.')

        with concurrent.futures.ThreadPoolExecutor() as executor:
            meta = executor.submit(extract_video_info, video_url).result()
        
        video_audio_streams = []
        for m in meta['formats']:
            file_size = m.get('filesize')
            if file_size is not None:
                file_size = f'{round(int(file_size) / 1000000, 2)} mb'

            resolution = 'Audio'
            if m.get('height') is not None:
                resolution = f"{m['height']}x{m['width']}"

            video_audio_streams.append({
                'resolution': resolution,
                'extension': m.get('ext'),
                'file_size': file_size,
                'video_url': m.get('url')
            })

        video_audio_streams = video_audio_streams[::-1]

        context = {
            'form': form,
            'title': meta.get('title'),
            'streams': video_audio_streams,
            'description': meta.get('description'),
            'likes': meta.get('like_count'),
            'dislikes': meta.get('dislike_count'),
            'thumb': meta.get('thumbnails', [{}])[3].get('url'),
            'duration': round(int(meta.get('duration', 0)) / 60, 2),
            'views': f'{int(meta.get("view_count", 0)):,}'
        }
        return render(request, 'home.html', context)

    return render(request, 'home.html', {'form': form})
