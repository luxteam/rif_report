function timeFormatter(value, row, index, field) {
    var time = new Date(null);
    time.setSeconds(value);
    return time.toISOString().substr(11, 8);
}

function statusFormatter(value, row, index, field) {
    switch(value) {
    	case 'completed':
    		return 'Passed'
    		break
    	case 'failure':
    		return 'Failures'
    		break
    	case 'error':
    		return 'Errors'
    		break
    	case 'suppressed':
    		return 'Disabled'
    		break
    }
    return 'Unknown'
}