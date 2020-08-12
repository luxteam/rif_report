function timeFormatter(value, row, index, field) {
    let seconds = Math.floor(value / 1000)
    let millisecods = Math.floor(value % 1000)
    return `${seconds}s ${millisecods}ms`
}

function searchTextInBootstrapTable(status) {
    $('.content-container [id]').bootstrapTable('resetSearch', status);
}