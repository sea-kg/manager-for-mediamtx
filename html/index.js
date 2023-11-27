function human_file_size(bytes, si=false, dp=1) {
    const thresh = si ? 1000 : 1024;
    if (Math.abs(bytes) < thresh) {
      return bytes + ' B';
    }
    const units = si
      ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'] 
      : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
    let u = -1;
    const r = 10**dp;
    do {
      bytes /= thresh;
      ++u;
    } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);
    return bytes.toFixed(dp) + ' ' + units[u];
}


function update_video_files() {
    $.ajax({
        url: '/api/video-files',
        method: 'get',
        dataType: 'json',
        // data: {text: 'Текст'},     /* Параметры передаваемые в запросе. */
    }).done(function(data) {
        var elem = document.getElementById('list_of_files');
        for (var i in data.list) {
            var file_info = data.list[i];
            console.log(file_info);
            var new_elem_id = "video_file_" + file_info.name;
            if (document.getElementById(new_elem_id) === null) {
                _html = '<div class="video-file-info" id="' + new_elem_id + '">' + file_info.name + ' (' + human_file_size(file_info.size_in_bytes) + ')</div>';
                elem.innerHTML += _html;
            }
        }
    });
}


document.addEventListener("DOMContentLoaded", function(event) {
    update_video_files();
});