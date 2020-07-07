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
    		return 'Failured'
    		break
    	case 'error':
    		return 'Error'
    		break
    	case 'suppressed':
    		return 'Skipped'
    		break
    }
    return 'Unknown'
}