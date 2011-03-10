var state = {
	"stopped": false
};

function setImmediateInterval(func, ival) {
	func();
	setInterval(func, ival);
}

function formatFloat(num) {
	if (typeof num === "string") {
		return num;
	}
	var s = "";
	s += parseInt(num);
	mantissa = parseInt(num * 100) % 100;
	if (mantissa === 0) {
		return s + ".00";
	} else if (mantissa < 10) {
		return s + ".0" + mantissa;
	} else {
		return s + "." + mantissa;
	}
}

$(document).ready(function () {

	if (state.stopped) {
		$('#status_img').attr('src', '/static/img/octagon.png');
		$('#status_text').
			removeClass('green').
			addClass('red').
			text('Stopped');
	} else {
		$('#status_img').attr('src', '/static/img/circle.png');
		$('#status_text').
			addClass('green').
			removeClass('red').
			text('Running');
	}

	// update "resources" once a second
	setImmediateInterval(function () {
		$.get('/resources', function (data) {
			var userCPU = "unknown";
			var systemCPU = "unknown";
			if (state.lastUserCPU) {
				// TODO: correct for setInterval error
				userCPU = 100 * (data.rusage.ru_utime - state.lastUserCPU);
			}
			if (state.lastSystemCPU) {
				systemCPU = 100 * (data.rusage.ru_stime - state.lastSystemCPU);
			}

			$('#resources-cpu-usertime').text(formatFloat(userCPU) + "%");
			$('#resources-cpu-systemtime').text(formatFloat(systemCPU) + "%");
			$('#resources-memory-vsz').text(formatFloat(data.memory.virt));
			$('#resources-memory-rss').text(formatFloat(data.memory.res));
			$('#resources-memory-shr').text(formatFloat(data.memory.shr));

			state.lastUserCPU = data.rusage.ru_utime;
			state.lastSystemCPU = data.rusage.ru_stime;
		});
	}, 1000);

	setImmediateInterval(function () {
		$.get('/poll_frame_queue', function (data) {
			$('#active_frame > *').remove();
			if (data.stopped) {
				$('#active_frame').
					append('File ').
					append($('<code></code>').text(data.co_filename)).
					append(' line ').
					append($('<code></code>').text(data.f_lineno));
			} else {
				$('#active_frame').text('(not stopped)');
			}
		});
	}, 100);

});
