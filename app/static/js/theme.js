(function ()
{
    const storageKey =
        "workflow-theme";

    const root =
        document.documentElement;


    function applyTheme(theme)
    {
        root.setAttribute(
            "data-theme",
            theme
        );

        document
            .querySelectorAll(
                ".theme-icon"
            )
            .forEach(
                function (icon)
                {
                    if (theme === "light")
                    {
                        icon.className =
                            "bi bi-sun-fill theme-icon";
                    }
                    else
                    {
                        icon.className =
                            "bi bi-moon-stars-fill theme-icon";
                    }
                }
            );
    }


    const savedTheme =
        localStorage.getItem(
            storageKey
        )
        || "dark";


    applyTheme(
        savedTheme
    );


    document
        .querySelectorAll(
            ".theme-toggle"
        )
        .forEach(
            function (button)
            {
                button.addEventListener(
                    "click",
                    function ()
                    {
                        const current =
                            root.getAttribute(
                                "data-theme"
                            );

                        const next =
                            current === "dark"
                            ? "light"
                            : "dark";

                        localStorage.setItem(
                            storageKey,
                            next
                        );

                        applyTheme(
                            next
                        );
                    }
                );
            }
        );

})();