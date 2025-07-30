document.body.append(document.createElement("aside"));

setInterval(async () => {
    const [currentlyLaunching, results] = await fetch("/status").then((v) => v.json());

    results.reverse();

    const [last, beforeLast] = [
        ...(currentlyLaunching ? [[currentlyLaunching]] : []),
        ...results.map(([v, err]) => [v, err]),
    ];

    document.querySelector("aside").innerHTML = `
        <div id="before-last">
            <div class="chip" data-type="${!beforeLast[1] ? 'ok' : 'error'}"></div>
            <code>${beforeLast[0]}</code>
        </div>
        <div id="last">
            <div class="chip" data-type="${last[1] == null ? 'pending' : !last[1] ? 'ok' : 'error'}"></div>
            <code>${last[0]}</code>
        </div>
    `;
}, 100);
