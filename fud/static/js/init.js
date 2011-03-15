var state = {
	"stopped": false,
	"pollInterval": null
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

	var toggleState = function (newState) {
		state.stopped = newState;
		if (newState) {
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
	};
	toggleState();

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

	/* remove all child nodes and text from #active_frame */
	var clearActiveFrame = function () {
		$('#active_frame').children().remove();
		$('#active_frame').text('');
	};

	var pollUntilStopped = function () {
		$.get('/poll_frame_queue', function (data) {
			console.info(data.stopped);
			if (data.stopped && state.stopped === true) {
				/* race condition, happens when the callback below is scheduled
				 * while the trace is stopping.
				 */
				state.stopped = true;
			} else if (data.stopped && state.stopped == false) {
				toggleState(true);
				clearInterval(state.pollInterval);
				

				/* add the tb information */
				clearActiveFrame();
				$('#active_frame').
					append('File ').
					append($('<code></code>').text(data.co_filename)).
					append(' line ').
					append($('<code></code>').text(data.f_lineno));

				$('#continue_button').remove(); /* should be a no-op, but just in case */
				$('#frame_button_container').append(
					$('<button id="continue_button"></button>').
						text('continue').
						click(function () {
							/* mark the state as stopped, and start polling again */
							$.post('/continue', function (data) {
								toggleState(false);
								clearActiveFrame();
								$('#active_frame').text('nothing to see here');
								state.pollInterval = setInterval(pollUntilStopped, 100);
							});
						}));
				}
		});
	};

	/* should always be true */
	if (!state.stopped) {
		state.pollInterval = setInterval(pollUntilStopped, 100);
	}
});
