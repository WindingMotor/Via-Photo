document.addEventListener('DOMContentLoaded', function() {
    const galleryGrid = document.getElementById('galleryGrid');
    const sortBySelect = document.getElementById('sortBy');
    
    // Get all gallery items
    const getAllItems = () => {
        return Array.from(galleryGrid.querySelectorAll('.gallery-item'));
    };
    
    // Apply sorting
    function applySorting() {
        const items = getAllItems();
        const sortBy = sortBySelect.value;
        
        // Sort items
        items.sort((a, b) => {
            const aName = a.querySelector('.photo-name').textContent;
            const bName = b.querySelector('.photo-name').textContent;
            
            // Extract size value from text (e.g., "3.2 MB" -> 3.2)
            const aSizeText = a.querySelector('.photo-size').textContent;
            const bSizeText = b.querySelector('.photo-size').textContent;
            const aSizeMatch = aSizeText.match(/([\d.]+)/);
            const bSizeMatch = bSizeText.match(/([\d.]+)/);
            const aSize = aSizeMatch ? parseFloat(aSizeMatch[1]) : 0;
            const bSize = bSizeMatch ? parseFloat(bSizeMatch[1]) : 0;
            
            // Convert MB, KB to consistent units for comparison
            const aSizeUnit = aSizeText.includes('MB') ? 1 : aSizeText.includes('KB') ? 0.001 : 0.000001;
            const bSizeUnit = bSizeText.includes('MB') ? 1 : bSizeText.includes('KB') ? 0.001 : 0.000001;
            const aSizeNormalized = aSize * aSizeUnit;
            const bSizeNormalized = bSize * bSizeUnit;
            
            // Get date from the date element
            const aDate = new Date(a.querySelector('.photo-date').textContent);
            const bDate = new Date(b.querySelector('.photo-date').textContent);
            
            switch (sortBy) {
                case 'name-asc':
                    return aName.localeCompare(bName);
                case 'name-desc':
                    return bName.localeCompare(aName);
                case 'size-asc':
                    return aSizeNormalized - bSizeNormalized;
                case 'size-desc':
                    return bSizeNormalized - aSizeNormalized;
                case 'date-asc':
                    return aDate - bDate;
                case 'date-desc':
                    return bDate - aDate;
                default:
                    return 0;
            }
        });
        
        // Remove all items from the grid
        galleryGrid.innerHTML = '';
        
        // Add sorted items back
        items.forEach(item => {
            galleryGrid.appendChild(item);
        });
    }
    
    // Add event listener for auto-apply
    sortBySelect.addEventListener('change', applySorting);
    
    // Initial sort on page load
    applySorting();
});
