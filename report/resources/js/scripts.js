function timeFormatter(value, row, index, field) {
    var time = new Date(null);
    time.setSeconds(value);
    return time.toISOString().substr(11, 8);
}

function searchTextInBootstrapTable(status) {
    $('.content-container [id]').bootstrapTable('resetSearch', status);
}